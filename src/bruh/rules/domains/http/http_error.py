"""Diagnostic rule for HTTP and network gateway errors (502, 504, 401, 403, 500, ETIMEDOUT)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch
from bruh.engine.extractors import FactExtractor

HTTP_STATUS_LINE_REGEX = re.compile(
    r"(?:HTTP/[123](?:\.\d)?\s+(?P<code>502|504|503|401|403|500)\b(?:\s+(?P<status>[^\r\n]+))?|"
    r"\b(?P<c502>502\s+Bad\s+Gateway)\b|"
    r"\b(?P<c504>504\s+Gateway\s+Time-?out)\b|"
    r"\b(?P<c401>401\s+Unauthorized)\b|"
    r"\b(?P<c403>403\s+Forbidden)\b|"
    r"\b(?P<c500>500\s+Internal\s+Server\s+Error)\b)",
    re.IGNORECASE
)

class HttpErrorRule(BaseDiagnosticRule):
    """Diagnoses common HTTP status failures and reverse proxy gateway issues."""

    rule_id = "http-error"
    name = "HTTP / Network Gateway Error"
    category = "network"
    priority = 75

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        match = HTTP_STATUS_LINE_REGEX.search(cleaned_output)
        if match:
            code = match.group("code")
            status_text = match.group("status") or ""
            
            if not code:
                if match.group("c502"):
                    code = "502"
                    status_text = "Bad Gateway"
                elif match.group("c504"):
                    code = "504"
                    status_text = "Gateway Timeout"
                elif match.group("c401"):
                    code = "401"
                    status_text = "Unauthorized"
                elif match.group("c403"):
                    code = "403"
                    status_text = "Forbidden"
                elif match.group("c500"):
                    code = "500"
                    status_text = "Internal Server Error"
                else:
                    code = "HTTP Error"

            status_display = status_text.strip() if status_text else ""
            if not status_display:
                if code == "502":
                    status_display = "Bad Gateway"
                elif code == "504":
                    status_display = "Gateway Timeout"
                elif code == "401":
                    status_display = "Unauthorized"
                elif code == "403":
                    status_display = "Forbidden"
                elif code == "500":
                    status_display = "Internal Server Error"

            title = f"💀 HTTP {code} {status_display}".strip()
            headline = f"HTTP {code} means a server acting as a gateway or proxy could not get a valid response from the upstream server." if code == "502" else f"HTTP {code} {status_display}"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=headline,
                extracted_vars={"code": code, "status": status_display, "command": command or ""}
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        code = vars.get("code")
        if code == "502":
            return "The request reached a server, but that server could not get a valid response from another server behind it."
        if code == "504":
            return "The gateway server timed out waiting for the upstream backend application to finish processing."
        if code == "401":
            return "The server rejected the request because valid authentication credentials were missing or invalid."
        if code == "403":
            return "The server understood your identity but denied permission to access this resource."
        if code == "500":
            return "The backend server encountered an unhandled exception or crash while processing the request."
        return "The HTTP request failed with an error status code from the server."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        code = vars.get("code")
        if code == "502":
            return [
                "Try the request again in a moment.",
                "Check whether the backend server or API is running.",
                "If you control the proxy, check its upstream configuration (e.g. nginx.conf)."
            ]
        if code == "504":
            return [
                "Try the request again in a moment.",
                "Check if the backend server is overloaded or stuck on a long task.",
                "Increase the proxy or client timeout limit if the query is expected to take time."
            ]
        if code in ("401", "403"):
            return [
                "Check your API key, token, or login credentials.",
                "Verify that authorization headers are properly attached to your request.",
                "Ensure your user account has permission to access this specific endpoint."
            ]
        return [
            "Check that the target server is running and reachable.",
            "Verify the request URL and query parameters.",
            "Check server error logs for more information."
        ]
