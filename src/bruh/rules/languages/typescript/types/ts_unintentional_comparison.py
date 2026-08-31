"""Diagnostic rule for TypeScript non-overlapping comparison errors (TS2367)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_UNINTENTIONAL_COMPARISON_REGEX = re.compile(
    r"error\s+TS2367:\s*This comparison appears to be unintentional because the types\s+'(?P<type1>[^']+)'\s+and\s+'(?P<type2>[^']+)'\s+have no overlap",
    re.IGNORECASE
)

class TSUnintentionalComparisonRule(BaseDiagnosticRule):
    """Diagnoses TypeScript comparisons between types with no overlap (TS2367)."""

    rule_id = "ts-unintentional-comparison"
    name = "TypeScript Unintentional Comparison"
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

        match = TS_UNINTENTIONAL_COMPARISON_REGEX.search(cleaned_output)
        if match:
            type1 = match.group("type1")
            type2 = match.group("type2")
            raw_err = match.group(0).strip()

            title = f"💀 Unintentional comparison: '{type1}' and '{type2}' have no overlap (TS2367)"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "type1": type1,
                    "type2": type2,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        type1 = vars.get("type1", "Type A")
        type2 = vars.get("type2", "Type B")
        return (
            f"You are comparing values of types '{type1}' and '{type2}'. "
            f"Because these types share no possible common values, the equality check will always produce the same boolean result."
        )

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        type1 = vars.get("type1", "type1")
        type2 = vars.get("type2", "type2")

        return [
            f"Check for typos in variable names, enum members, or literal values in the comparison.",
            f"If comparing string and numeric representations, convert one operand explicitly: `Number({type1}) === ...` or `String(...)`.",
            f"If a variable should hold both types, update its type annotation to a union: `({type1} | {type2})`."
        ]
