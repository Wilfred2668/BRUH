"""Diagnostic rule for TypeScript missing return value errors (TS2355, TS2366, TS7030)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_MISSING_RETURN_REGEX = re.compile(
    r"error\s+TS(?P<code>2355|2366|7030):\s*(?:A function whose declared type is neither [^\r\n]+must return a value|"
    r"Function lacks ending return statement[^\r\n]*|"
    r"Not all code paths return a value)",
    re.IGNORECASE
)

class TSMissingReturnRule(BaseDiagnosticRule):
    """Diagnoses TypeScript functions missing explicit return values on some or all execution branches (TS2355, TS2366, TS7030)."""

    rule_id = "ts-missing-return"
    name = "TypeScript Missing Return Statement"
    category = "compiler"
    priority = 82

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = TS_MISSING_RETURN_REGEX.search(cleaned_output)
        if match:
            code = match.group("code")
            raw_err = match.group(0).strip()

            title = f"💀 Function is missing a return statement (TS{code})"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "code": code,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        return (
            "The function signature declares a non-void return type, but one or more code paths "
            "reach the end of the function without executing a 'return' statement."
        )

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        return [
            "Add a `return <value>;` statement to all branching code paths (e.g. at the end of the function or inside `else`/`switch` blocks).",
            "If the function does not produce a value, change its return type annotation to `void`.",
            "If returning nothing is valid in some branches, update the return type to include `undefined` or `null` (e.g. `string | undefined`)."
        ]
