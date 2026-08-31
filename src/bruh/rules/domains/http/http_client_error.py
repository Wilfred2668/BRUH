"""Diagnostic rule for HTTP client transport, connection, and timeout errors."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

HTTP_CLIENT_ERR_REGEX = re.compile(
    r"(?:(?:requests\.exceptions\.ConnectionError:\s*(?P<req_conn>[^\r\n]+))|"
    r"(?:requests\.exceptions\.(?:ConnectTimeout|ReadTimeout|Timeout):\s*(?P<req_time>[^\r\n]+))|"
    r"(?:requests\.exceptions\.HTTPError:\s*(?P<req_http>[^\r\n]+))|"
    r"(?:httpx\.(?:ConnectTimeout|ReadTimeout|ConnectError):\s*(?P<htx_msg>[^\r\n]+))|"
    r"(?:urllib\.error\.URLError:\s*<urlopen error (?P<url_err>[^>]+)>)|"
    r"(?:AxiosError:\s*(?P<axios_msg>[^\r\n]+)))",
    re.IGNORECASE
)

class HttpClientErrorRule(BaseDiagnosticRule):
    """Diagnoses outbound HTTP request failures in Python (requests/httpx/urllib) and Node.js (Axios)."""

    rule_id = "http-client-error"
    name = "HTTP Client Request Failure"
    category = "network"
    priority = 76

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        # Prefer specific DNS/socket rule if it matched low-level socket.gaierror
        match = HTTP_CLIENT_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            req_conn = match.group("req_conn")
            req_time = match.group("req_time")
            req_http = match.group("req_http")
            htx_msg = match.group("htx_msg")
            url_err = match.group("url_err")
            axios_msg = match.group("axios_msg")

            is_timeout = bool(req_time or (htx_msg and "timeout" in raw_err.lower()) or "timeout" in raw_err.lower())

            if is_timeout:
                title = "💀 HTTP Client Timeout"
                kind = "timeout"
            elif req_http:
                title = f"💀 HTTP Client Error: {req_http.strip()}"
                kind = "http_error"
            elif axios_msg:
                title = f"💀 Axios Client Error: {axios_msg.strip()}"
                kind = "axios"
            else:
                title = "💀 HTTP Client Connection Failed"
                kind = "connection"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "kind": kind,
                    "raw": raw_err,
                    "detail": req_conn or req_time or req_http or htx_msg or url_err or axios_msg
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        kind = vars.get("kind")
        if kind == "timeout":
            return "The HTTP client attempted to send a web request or receive a response, but the remote server did not respond before the timeout expired."
        elif kind == "http_error":
            return "The remote HTTP server returned an unsuccessful HTTP status code in response to the request."
        
        return "The HTTP client could not establish a connection to the target server URL (network dropped, host unreachable, or connection refused)."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        kind = vars.get("kind")
        if kind == "timeout":
            return [
                "Increase the timeout limit in your request configuration (e.g. `requests.get(url, timeout=30)`).",
                "Verify that the destination server is online and not overloaded.",
                "Check if network latency or proxy configuration is delaying packets."
            ]

        return [
            "Verify that the request URL, protocol (http vs https), and port are correct.",
            "Check if the remote service or API server is running.",
            "Inspect your network connectivity, firewall, or corporate proxy settings."
        ]
