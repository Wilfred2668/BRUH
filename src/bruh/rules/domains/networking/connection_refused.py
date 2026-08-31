"""Diagnostic rule for network connection failures, timeouts, DNS errors, and socket resets."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch
from bruh.engine.extractors import FactExtractor

NETWORK_ERR_REGEX = re.compile(
    r"(?:(?:Could not resolve host:\s*(?P<dns_host>[^\s\r\n]+))|"
    r"(?:getaddrinfo\s+(?:ENOTFOUND|EAI_AGAIN)\s*(?P<dns_host2>[^\s\r\n]+))|"
    r"(?:getaddrinfo\s*failed|Name or service not known|socket\.gaierror|\[(?:Errno 11001|Errno -2|Errno -3)\])|"
    r"(?:ECONNREFUSED\b|ConnectionRefusedError\b|\[(?:Errno 111|WinError 10061)\]\s*Connection refused)|"
    r"(?:TimeoutError\b|ConnectTimeoutError\b|socket\.timeout\b|ETIMEDOUT\b|\[(?:Errno 110|WinError 10060)\]|timed?\s*out)|"
    r"(?:ConnectionResetError\b|ECONNRESET\b|\[(?:Errno 104|WinError 10054)\]|Connection reset by peer)|"
    r"(?:EHOSTUNREACH\b))",
    re.IGNORECASE
)

class ConnectionRefusedRule(BaseDiagnosticRule):
    """Diagnoses network connection refused, timeout, socket reset, and DNS resolution errors."""

    rule_id = "connection-refused"
    name = "Connection Refused / Network Error"
    category = "network"
    priority = 70

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = NETWORK_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            combined_text = cleaned_output + "\n" + (command or "")
            out_lower = combined_text.lower()

            dns_host = match.group("dns_host") or match.group("dns_host2")
            if not dns_host and any(k in out_lower for k in ["could not resolve host", "enotfound", "gaierror", "name or service not known", "errno 11001"]):
                m_url = re.search(r"https?://(?P<url_host>[a-zA-Z0-9_\-\.]+)", combined_text, re.I)
                if m_url:
                    dns_host = m_url.group("url_host")

            host, port = FactExtractor.extract_host_and_port(combined_text)
            if not port:
                port = FactExtractor.extract_port(combined_text)
            if not host and "127.0.0.1" in combined_text:
                host = "127.0.0.1"
            elif not host and "localhost" in combined_text:
                host = "localhost"

            target_repr = dns_host if dns_host else (f"{host}:{port}" if host and port else (f"port {port}" if port else (host if host else "the server")))

            # Timeout extraction
            m_timeout = re.search(r"timeout[=\s]+(\d+(?:\.\d+)?)", combined_text, re.I)
            timeout_val = m_timeout.group(1) if m_timeout else None

            # Categorize error
            if dns_host or any(k in out_lower for k in ["could not resolve host", "enotfound", "gaierror", "name or service not known"]):
                kind = "dns"
                target_repr = dns_host or "domain name"
                title = f"💀 DNS Resolution Failed ({target_repr})"
                headline = f"Could not resolve host: {target_repr}"
            elif any(k in out_lower for k in ["timeouterror", "socket.timeout", "etimedout", "timed out", "connecttimeouterror", "winerror 10060", "errno 110"]):
                kind = "timeout"
                title = f"💀 Connection Timeout"
                if host and port:
                    title = f"💀 Connection Timeout ({host}:{port})"
                elif host:
                    title = f"💀 Connection Timeout ({host})"
                
                if timeout_val:
                    headline = f"The connection to {target_repr} did not respond within the {timeout_val} second timeout."
                else:
                    headline = f"The connection to {target_repr} timed out before receiving a response."
            elif any(k in out_lower for k in ["connectionreset", "econnreset", "reset by peer", "winerror 10054", "errno 104"]):
                kind = "reset"
                title = f"💀 Connection Reset ({target_repr})"
                headline = f"The remote host {target_repr} forcibly closed or reset the active connection."
            else:
                kind = "refused"
                title = f"💀 Connection Refused ({target_repr})"
                headline = f"No server or service is listening on {target_repr}."

            service = "Network Service"
            if port == 5432 or port == "5432":
                service = "PostgreSQL"
            elif port == 3306 or port == "3306":
                service = "MySQL"
            elif port == 6379 or port == "6379":
                service = "Redis"
            elif port == 27017 or port == "27017":
                service = "MongoDB"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=headline,
                extracted_vars={
                    "kind": kind,
                    "host": host,
                    "dns_host": dns_host,
                    "port": str(port) if port else None,
                    "service": service,
                    "target": target_repr,
                    "timeout": timeout_val,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        kind = vars.get("kind", "refused")
        target = vars.get("target", "the server")
        timeout = vars.get("timeout")
        dns_host = vars.get("dns_host")

        if kind == "dns":
            host_str = dns_host if dns_host else target
            return f"Your system could not resolve the domain name '{host_str}' to an IP address. Check your internet connection or verify the domain name spelling."
        elif kind == "timeout":
            if timeout:
                return f"Your program tried to connect to {target}, but no response arrived within {timeout} seconds."
            return f"Your program tried to connect to {target}, but no response arrived before the timeout."
        elif kind == "reset":
            return f"The connection to {target} was established, but the remote server closed or crashed during the request."
        
        return f"Your program tried to connect to {target}, but nothing is currently listening on that address."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        kind = vars.get("kind", "refused")
        target = vars.get("target", "the server")
        dns_host = vars.get("dns_host")

        if kind == "dns":
            host_str = dns_host if dns_host else target
            return [
                "Check your internet connection.",
                f"Verify the spelling of the domain name: '{host_str}'.",
                "Check your DNS server or network settings."
            ]
        elif kind == "timeout":
            return [
                f"Check that {target} is running and reachable.",
                "Verify the host address and port are correct.",
                "Try connecting again with a longer timeout if the server is slow or busy."
            ]
        elif kind == "reset":
            return [
                "Check server logs for crashes or unhandled exceptions.",
                "Verify that the request payload was not too large for the server.",
                "Make sure your client and server are using matching protocol versions (HTTP vs HTTPS)."
            ]

        return [
            f"Make sure the target server/database is running on {target}.",
            "Check for typos in the host address or port number.",
            "Verify your local firewall or network settings permit this connection."
        ]
