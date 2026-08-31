"""Diagnostic rule for TypeScript syntax and parser errors (TS1000-series)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_SYNTAX_ERROR_REGEX = re.compile(
    r"error\s+TS(?P<code>1\d{3}):\s*(?P<msg>[^\r\n]+)",
    re.IGNORECASE
)

class TSSyntaxErrorRule(BaseDiagnosticRule):
    """Diagnoses TypeScript parser and compiler syntax errors (TS1000-series)."""

    rule_id = "ts-syntax-error"
    name = "TypeScript Syntax Error"
    category = "syntax"
    priority = 80

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = TS_SYNTAX_ERROR_REGEX.search(cleaned_output)
        if match:
            code = match.group("code")
            msg = match.group("msg").strip()
            raw_err = match.group(0).strip()

            title = f"💀 TypeScript Syntax Error: {msg} (TS{code})"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "code": code,
                    "msg": msg,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        msg = vars.get("msg", "Syntax error")
        return f"TypeScript encountered invalid syntax or grammar: '{msg}'."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        msg = vars.get("msg", "")

        suggestions = [
            "Check the exact file line and column indicated by the compiler.",
            "Verify all opening brackets `(`, `{`, `[` and quotes have matching closing pairs."
        ]

        if "expected" in msg.lower():
            suggestions.append(f"Add the missing token or expression indicated in the compiler error: '{msg}'.")

        suggestions.append("Verify you are using valid TypeScript syntax for type annotations, generics, and variable declarations.")
        return suggestions
