"""Diagnostic rule for Python JSON parsing and decoding errors."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

PYTHON_JSON_ERR_REGEX = re.compile(
    r"(?:(?:json\.decoder\.JSONDecodeError:\s*(?P<py_msg>[^:]+):\s*line\s*(?P<py_line>\d+)\s*column\s*(?P<py_col>\d+))|"
    r"(?:JSONDecodeError:\s*(?P<py_msg2>[^\r\n]+)))",
    re.IGNORECASE
)

class JSONDecodeErrorRule(BaseDiagnosticRule):
    """Diagnoses malformed JSON syntax errors in Python json.loads() and json.load()."""

    rule_id = "json-decode-error"
    name = "Python JSONDecodeError"
    category = "runtime"
    priority = 77

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = PYTHON_JSON_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            py_msg = match.group("py_msg") or match.group("py_msg2")
            py_line = match.group("py_line")
            py_col = match.group("py_col")

            if py_msg and py_line and py_col:
                title = f"💀 JSONDecodeError: {py_msg.strip()} (line {py_line}, col {py_col})"
            elif py_msg:
                title = f"💀 JSONDecodeError: {py_msg.strip()}"
            else:
                title = "💀 JSONDecodeError: invalid JSON syntax"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "py_msg": py_msg,
                    "py_line": py_line,
                    "py_col": py_col,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        py_line = vars.get("py_line")
        py_col = vars.get("py_col")
        py_msg = vars.get("py_msg")

        if py_line and py_col:
            return f"The Python JSON parser encountered invalid syntax ({py_msg or 'malformed JSON'}) at line {py_line}, column {py_col}."
        
        return "The Python json module attempted to decode a string as JSON, but the string contained invalid JSON syntax."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        py_line = vars.get("py_line")
        py_col = vars.get("py_col")
        location_hint = f"around line {py_line}, column {py_col}" if py_line and py_col else "in the JSON string"

        return [
            f"Check the JSON payload {location_hint} for syntax issues (such as trailing commas, single quotes, or missing brackets).",
            "Ensure all dictionary keys and string values use double quotes (`\"key\": \"value\"`), as JSON does not support single quotes.",
            "If reading from an HTTP API response, verify the server returned a JSON payload instead of an HTML error page."
        ]
