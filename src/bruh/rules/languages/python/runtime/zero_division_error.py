"""Diagnostic rule for division by zero errors."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

ZERO_DIV_REGEX = re.compile(
    r"(?:(?:ZeroDivisionError:\s*(?:division by zero|integer division or modulo by zero|float division by zero))|"
    r"(?:division by zero)|"
    r"(?:divide by zero))",
    re.IGNORECASE
)

class ZeroDivisionErrorRule(BaseDiagnosticRule):
    """Diagnoses mathematical division or modulo by zero."""

    rule_id = "zero-division-error"
    name = "Division by zero"
    category = "runtime"
    priority = 76

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = ZERO_DIV_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            return RuleMatch(
                matched=True,
                title="💀 Division by zero (ZeroDivisionError)",
                original_error=raw_err,
                extracted_vars={"raw": raw_err}
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        return "Your code attempted to divide a number by zero or perform modulo with zero, which is mathematically undefined."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        return [
            "Check the denominator (divisor) variable right before the division to ensure it is not 0.",
            "Add a check before dividing (e.g. `if divisor != 0:`).",
            "Provide a default fallback value if the divisor can be zero."
        ]
