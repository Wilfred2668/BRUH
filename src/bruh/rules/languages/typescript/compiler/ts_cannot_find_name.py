"""Diagnostic rule for TypeScript cannot find name errors (TS2304, TS2552)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_CANNOT_FIND_NAME_REGEX = re.compile(
    r"error\s+TS(?P<code>2304|2552):\s*Cannot find name\s+'(?P<name>[^']+)'(?:\.\s*Did you mean\s+'(?P<suggestion>[^']+)'\?)?",
    re.IGNORECASE
)

class TSCannotFindNameRule(BaseDiagnosticRule):
    """Diagnoses TypeScript undeclared identifier and cannot find name errors (TS2304, TS2552)."""

    rule_id = "ts-cannot-find-name"
    name = "TypeScript Cannot Find Name"
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

        match = TS_CANNOT_FIND_NAME_REGEX.search(cleaned_output)
        if match:
            code = match.group("code") or "2304"
            name = match.group("name")
            suggestion = match.group("suggestion")
            raw_err = match.group(0).strip()

            title = f"💀 Cannot find name '{name}' (TS{code})"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "code": code,
                    "name": name,
                    "suggestion": suggestion,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        name = vars.get("name", "identifier")
        return f"TypeScript cannot resolve identifier '{name}' in the current file or global scope."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        name = vars.get("name", "identifier")
        suggestion = vars.get("suggestion")

        suggestions = []
        if suggestion:
            suggestions.append(f"Did you mean '{suggestion}'? Check the spelling of '{name}'.")
        else:
            suggestions.append(f"Check for typos in the identifier name '{name}'.")

        suggestions.append(f"Declare the variable or type before using it: `const {name} = ...` or `let {name}: ...`.")
        suggestions.append(f"If '{name}' is defined in another file or npm library, add the missing `import` declaration.")
        suggestions.append(f"If '{name}' is a global browser/Node API (e.g. `document`, `process`), verify `lib` compiler options or install `@types/node`.")
        return suggestions
