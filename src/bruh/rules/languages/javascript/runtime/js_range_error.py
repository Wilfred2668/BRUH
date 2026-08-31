"""Diagnostic rule for JavaScript / Node.js RangeError."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

JS_RANGE_ERR_REGEX = re.compile(
    r"(?:RangeError:\s*(?P<msg>Maximum call stack size exceeded|Invalid array length|Invalid count value|.*))",
    re.IGNORECASE
)

class JSRangeErrorRule(BaseDiagnosticRule):
    """Diagnoses maximum call stack exhaustion and numeric range violations in JavaScript / Node.js."""

    rule_id = "js-range-error"
    name = "JavaScript RangeError"
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

        match = JS_RANGE_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            msg = match.group("msg") or ""

            if "maximum call stack size exceeded" in msg.lower():
                title = "💀 RangeError: Maximum call stack size exceeded"
            elif msg:
                title = f"💀 RangeError: {msg.strip()}"
            else:
                title = "💀 JavaScript RangeError"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={"msg": msg, "raw": raw_err}
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        msg = vars.get("msg", "").lower()
        if "maximum call stack" in msg:
            return (
                "A JavaScript function called itself repeatedly without reaching a valid terminating base case, "
                "overflowing the V8 engine's maximum call stack size limit."
            )
        elif "invalid array length" in msg:
            return "An attempt was made to create an Array with an invalid length (e.g. negative number or floating point)."

        return "A value or argument passed to a JavaScript function was outside the allowed numerical range."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        msg = vars.get("msg", "").lower()
        if "maximum call stack" in msg:
            return [
                "Inspect your recursive functions for a missing, incorrect, or unreachable base case.",
                "Ensure recursive arguments advance toward the base case with each invocation (e.g. `n - 1`).",
                "Refactor deep recursion into an iterative loop (`while`/`for`) using a local stack or queue."
            ]
        elif "invalid array length" in msg:
            return [
                "Ensure array length constructor arguments are non-negative integers: `new Array(Math.max(0, Math.floor(len)))`.",
                "Check variable calculations that produce the array length."
            ]

        return [
            "Check function arguments against expected range constraints.",
            "Verify numerical calculations prior to calling built-in methods."
        ]
