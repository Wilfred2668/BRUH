"""Diagnostic rule for TypeScript property does not exist errors (TS2339)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_PROPERTY_NOT_FOUND_REGEX = re.compile(
    r"error\s+TS2339:\s*Property\s+'(?P<prop>[^']+)'\s+does not exist on type\s+'(?P<target_type>[^']+)'(?:\.\s*Did you mean\s+'(?P<suggestion>[^']+)'\?)?",
    re.IGNORECASE
)

class TSPropertyNotFoundRule(BaseDiagnosticRule):
    """Diagnoses TypeScript property does not exist errors on types/interfaces (TS2339)."""

    rule_id = "ts-property-not-found"
    name = "TypeScript Property Not Found"
    category = "types"
    priority = 80

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = TS_PROPERTY_NOT_FOUND_REGEX.search(cleaned_output)
        if match:
            prop = match.group("prop")
            target_type = match.group("target_type")
            suggestion = match.group("suggestion")
            raw_err = match.group(0).strip()

            title = f"💀 Property '{prop}' does not exist on type '{target_type}' (TS2339)"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "prop": prop,
                    "target_type": target_type,
                    "suggestion": suggestion,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        prop = vars.get("prop", "property")
        target_type = vars.get("target_type", "type")
        return f"The TypeScript compiler checked type '{target_type}', but found no declaration or definition for property '{prop}'."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        prop = vars.get("prop", "property")
        target_type = vars.get("target_type", "type")
        suggestion = vars.get("suggestion")

        suggestions = []
        if suggestion:
            suggestions.append(f"Did you mean '{suggestion}'? Check the spelling of '{prop}'.")
        else:
            suggestions.append(f"Check for typos in the property name '{prop}'.")

        suggestions.append(f"Add the missing property to interface/type '{target_type}': `{prop}?: ...` or `{prop}: ...`.")
        suggestions.append(f"If '{target_type}' is a union type, narrow the type using a type guard (`if ('{prop}' in obj)` or `typeof`).")
        return suggestions
