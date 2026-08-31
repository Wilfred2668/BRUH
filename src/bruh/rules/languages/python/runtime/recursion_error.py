"""Diagnostic rule for Python infinite recursion errors."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

PYTHON_RECURSION_ERR_REGEX = re.compile(
    r"RecursionError:\s*maximum recursion depth exceeded(?:\s*while (?P<rec_act>[^\r\n]+))?",
    re.IGNORECASE
)

class RecursionErrorRule(BaseDiagnosticRule):
    """Diagnoses maximum recursion depth exceeded in Python."""

    rule_id = "recursion-error"
    name = "Python RecursionError"
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

        match = PYTHON_RECURSION_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            rec_act = match.group("rec_act")

            if rec_act:
                title = f"💀 RecursionError: max depth exceeded while {rec_act.strip()}"
            else:
                title = "💀 RecursionError: maximum recursion depth exceeded"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={"raw": raw_err, "action": rec_act}
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        return "A Python function called itself repeatedly without reaching a valid base case (stopping condition), exceeding Python's maximum recursion limit."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        return [
            "Check your recursive functions for a missing, incorrect, or unreachable base case (stopping condition).",
            "Verify that function arguments advance toward the base case with each recursive call (e.g. `n - 1`).",
            "For large recursive structures, refactor the algorithm to use an iterative loop with a stack or queue."
        ]
