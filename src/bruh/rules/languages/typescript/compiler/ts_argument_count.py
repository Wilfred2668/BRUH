"""Diagnostic rule for TypeScript argument count errors (TS2554, TS2555)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_ARG_COUNT_REGEX = re.compile(
    r"error\s+TS(?:2554|2555):\s*Expected\s+(?P<expected>[0-9\-]+|at least [0-9]+)\s+arguments?,\s+but got\s+(?P<got>\d+)",
    re.IGNORECASE
)

class TSArgumentCountRule(BaseDiagnosticRule):
    """Diagnoses TypeScript wrong number of arguments passed to functions (TS2554, TS2555)."""

    rule_id = "ts-argument-count"
    name = "TypeScript Argument Count"
    category = "compiler"
    priority = 80

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = TS_ARG_COUNT_REGEX.search(cleaned_output)
        if match:
            expected = match.group("expected")
            got = match.group("got")
            raw_err = match.group(0).strip()

            title = f"💀 Expected {expected} argument(s), but got {got} (TS2554)"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "expected": expected,
                    "got": got,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        expected = vars.get("expected", "correct number of")
        got = vars.get("got", "different number of")
        return f"The function signature expects {expected} argument(s), but the invocation provided {got}."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        expected = vars.get("expected", "expected number of")
        got = vars.get("got", "provided number of")

        return [
            f"Update the function call to supply all {expected} required argument(s).",
            "Mark optional parameters in the function definition with `?` or provide default values (e.g. `param: type = defaultValue`).",
            "Use a rest parameter `(...args: type[])` if the function should accept a variable number of arguments."
        ]
