"""Diagnostic rule for port/address collision errors."""

import re
import sys
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

PORT_IN_USE_REGEX = re.compile(
    r"(?:(?:EADDRINUSE|address already in use|Address already in use|Only one usage of each socket address)"
    r".*?(?:(?:::|127\.0\.0\.1|0\.0\.0\.0|localhost):(?P<port1>\d+)|port (?P<port2>\d+)|:(?P<port3>\d+))|"
    r"(?:Port\s+(?P<port4>\d+)\s+is already in use))",
    re.IGNORECASE | re.DOTALL
)

GENERIC_EADDRINUSE = re.compile(
    r"(?:EADDRINUSE|\[Errno 98\] Address already in use|\[Errno 48\] Address already in use|\[WinError 10048\])",
    re.IGNORECASE
)

class PortInUseRule(BaseDiagnosticRule):
    """Diagnoses port and socket address binding collisions."""

    rule_id = "port-already-in-use"
    name = "Port Already In Use"
    category = "network"
    priority = 95

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        match = PORT_IN_USE_REGEX.search(cleaned_output)
        if match:
            port = (
                match.group("port1") or
                match.group("port2") or
                match.group("port3") or
                match.group("port4") or
                "unknown"
            )
            code = "EADDRINUSE" if "EADDRINUSE" in cleaned_output else "Address already in use"
            return RuleMatch(
                matched=True,
                title=f"💀 Port {port} already in use" if port != "unknown" else "💀 Port already in use",
                original_error=match.group(0).strip().splitlines()[0],
                extracted_vars={
                    "port": port,
                    "code": code
                }
            )

        generic_match = GENERIC_EADDRINUSE.search(cleaned_output)
        if generic_match:
            port_finder = re.search(r":(\d{2,5})\b|port\s+(\d{2,5})", cleaned_output, re.IGNORECASE)
            port = "unknown"
            if port_finder:
                port = port_finder.group(1) or port_finder.group(2)

            return RuleMatch(
                matched=True,
                title=f"💀 Port {port} already in use" if port != "unknown" else "💀 Port already in use",
                original_error=generic_match.group(0),
                extracted_vars={
                    "port": port,
                    "code": generic_match.group(0)
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        port = vars.get("port", "the specified port")
        if port != "unknown":
            return f"Your app tried to use port {port}, but another program is already running on it."
        return "Your app tried to use a network port that is already in use by another program."

    def generate_human_explanation(self, vars: Dict[str, Any]) -> str:
        port = vars.get("port", "the port")
        if port != "unknown":
            return (
                f"You're trying to park your server in space #{port},\n"
                "but a server from earlier is still parked there."
            )
        return "Two servers cannot listen on the exact same port at the same time."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        port = vars.get("port", "3000")
        is_windows = sys.platform == "win32"

        if port != "unknown":
            alt_port = str(int(port) + 1) if port.isdigit() else "3001"
            inspect_cmd = f"netstat -ano | findstr :{port}" if is_windows else f"lsof -i :{port}"
            return [
                f"Something is already using port {port}. Close the other server and try again.",
                f"If you can't find it, run: `{inspect_cmd}`",
                f"Or change your app to use port {alt_port}."
            ]
        
        inspect_fallback = "netstat -ano" if is_windows else "lsof -i"
        return [
            "Close any other dev servers running in other terminal tabs.",
            f"Find what's running on your ports: `{inspect_fallback}`",
            "Or change your app to use a different port."
        ]
