"""Diagnostic rule for TypeScript generic type constraint violations (TS2344)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_TYPE_CONSTRAINT_REGEX = re.compile(
    r"error\s+TS2344:\s*Type\s+'(?P<type>[^']+)'\s+does not satisfy the constraint\s+'(?P<constraint>[^']+)'",
    re.IGNORECASE
)

class TSTypeConstraintRule(BaseDiagnosticRule):
    """Diagnoses TypeScript generic type parameter constraint violations (TS2344)."""

    rule_id = "ts-type-constraint"
    name = "TypeScript Type Constraint Violation"
    category = "types"
    priority = 82

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = TS_TYPE_CONSTRAINT_REGEX.search(cleaned_output)
        if match:
            type_val = match.group("type")
            constraint = match.group("constraint")
            raw_err = match.group(0).strip()

            title = f"💀 Type '{type_val}' does not satisfy constraint '{constraint}' (TS2344)"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "type": type_val,
                    "constraint": constraint,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        type_val = vars.get("type", "type")
        constraint = vars.get("constraint", "constraint")
        return (
            f"The generic type parameter requires arguments that extend '{constraint}', "
            f"but the provided type argument '{type_val}' does not satisfy this requirement."
        )

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        type_val = vars.get("type", "type")
        constraint = vars.get("constraint", "constraint")

        return [
            f"Provide a type argument that satisfies `{constraint}` (e.g. implements required fields/methods).",
            f"Widen the generic definition's `extends` constraint if `{type_val}` should also be supported: `<T extends {constraint} | {type_val}>`.",
            f"Check if `{type_val}` needs additional properties or type casting to fulfill the constraint."
        ]
