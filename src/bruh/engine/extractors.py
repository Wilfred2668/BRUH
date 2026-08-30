"""Dynamic fact and entity extraction utilities for error output parsing."""

import re
from typing import Optional, Tuple, Dict, Any, List
from pathlib import Path

# Regex patterns for reusable fact extraction
PORT_PATTERN = re.compile(
    r"(?:(?:port|addr|address|listen|binding)[:\s]+(?:\*{1,2}|0\.0\.0\.0|127\.0\.0\.1|localhost|:::)?:?(?P<p1>\d{2,5})\b|"
    r":(?P<p2>\d{2,5})\b|"
    r"\b(?:EADDRINUSE|EACCES|listen)\b.*?[:\s](?P<p3>\d{2,5})\b)",
    re.IGNORECASE
)

HOST_PORT_PATTERN = re.compile(
    r"(?:(?P<host>localhost|127\.0\.0\.1|0\.0\.0\.0|[a-zA-Z0-9_\-\.]+):(?P<port>\d{2,5})\b|"
    r"\(['\"](?P<h_tup>localhost|127\.0\.0\.1|0\.0\.0\.0|[a-zA-Z0-9_\-\.]+)['\"]\s*,\s*(?P<p_tup>\d{2,5})\))",
    re.IGNORECASE
)

HTTP_CODE_PATTERN = re.compile(
    r"(?:(?:HTTP|status|code|response)[:\s]*(?P<c1>[45]\d{2})\b|"
    r"\b(?P<c2>502|503|504|400|401|403|404|408|429|500)\b\s+(?:Bad Gateway|Gateway Timeout|Service Unavailable|Unauthorized|Forbidden|Not Found|Internal Server Error)|"
    r"\b(?P<c3>ECONNRESET|ECONNREFUSED|ETIMEDOUT|EHOSTUNREACH|ENOTFOUND)\b)",
    re.IGNORECASE
)

DB_PATTERN = re.compile(
    r"(?:(?P<pg>postgres(?:ql)?|psycopg2?|pg_hba\.conf)|"
    r"(?P<mysql>mysql|mariadb|pymysql)|"
    r"(?P<redis>redis|ioredis)|"
    r"(?P<mongo>mongodb|mongoose|pymongo)|"
    r"(?P<sqlite>sqlite3?|database is locked))",
    re.IGNORECASE
)

class FactExtractor:
    """Extracts verified parameters, ports, paths, codes, and names from error texts."""

    @staticmethod
    def extract_port(text: str) -> Optional[int]:
        """Extract a network port number (1-65535) from error output."""
        if not text:
            return None
        for match in PORT_PATTERN.finditer(text):
            p_str = match.group("p1") or match.group("p2") or match.group("p3")
            if p_str:
                try:
                    port = int(p_str)
                    if 1 <= port <= 65535:
                        return port
                except ValueError:
                    continue
        return None

    @staticmethod
    def extract_host_and_port(text: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract host and port pair (e.g. 127.0.0.1:5432 or ('localhost', 8080))."""
        if not text:
            return None, None
        match = HOST_PORT_PATTERN.search(text)
        if match:
            host = match.group("host") or match.group("h_tup")
            p_str = match.group("port") or match.group("p_tup")
            try:
                port = int(p_str)
                if 1 <= port <= 65535:
                    return host, port
            except ValueError:
                pass
        return None, None

    @staticmethod
    def extract_http_code(text: str) -> Optional[str]:
        """Extract HTTP status code or socket error symbol (e.g. 502, 401, ECONNRESET)."""
        if not text:
            return None
        match = HTTP_CODE_PATTERN.search(text)
        if match:
            return match.group("c1") or match.group("c2") or match.group("c3")
        return None

    @staticmethod
    def extract_database_type(text: str) -> Optional[str]:
        """Identify if an error originates from PostgreSQL, MySQL, Redis, MongoDB, or SQLite."""
        if not text:
            return None
        match = DB_PATTERN.search(text)
        if match:
            if match.group("pg"):
                return "PostgreSQL"
            if match.group("mysql"):
                return "MySQL"
            if match.group("redis"):
                return "Redis"
            if match.group("mongo"):
                return "MongoDB"
            if match.group("sqlite"):
                return "SQLite"
        return None

    @staticmethod
    def extract_package_name(text: str) -> Optional[str]:
        """Extract package name from pip or npm install outputs."""
        if not text:
            return None
        # Pip distribution
        m_pip = re.search(r"(?:No matching distribution found for|satisfies the requirement)\s+([a-zA-Z0-9_\-\.]+)", text, re.I)
        if m_pip:
            return m_pip.group(1).strip()
        # npm 404
        m_npm = re.search(r"(?:registry\.npmjs\.org/|npm error 404 Not Found.*?')([a-zA-Z0-9_\-\.\@\/]+)", text, re.I)
        if m_npm:
            return m_npm.group(1).strip("'\"")
        return None

    @staticmethod
    def extract_missing_attribute(text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract type and attribute name from AttributeError or Cannot read properties of undefined.
        
        Returns (type_name, attribute_name).
        """
        if not text:
            return None, None
        
        # Python: 'NoneType' object has no attribute 'get'
        m_py = re.search(r"'(?P<type>[^']+)' object has no attribute '(?P<attr>[^']+)'", text)
        if m_py:
            return m_py.group("type"), m_py.group("attr")
        
        # JS: Cannot read property 'foo' of undefined / Cannot read properties of null (reading 'foo')
        m_js = re.search(r"Cannot read propert(?:y|ies) of (?P<type>undefined|null)(?:.*?reading '(?P<attr>[^']+)')?", text, re.I)
        if m_js:
            return m_js.group("type"), m_js.group("attr")
            
        return None, None
