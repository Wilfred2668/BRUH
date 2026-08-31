"""Diagnostic rule for TypeScript cannot assign to read-only or constant errors (TS2540, TS2588)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_READONLY_ASSIGNMENT_REGEX = re.compile(
    r"error\s+TS(?P<code>2540|2588):\s*Cannot assign to\s+'(?P<target>[^']+)'\s+because it is a\s+(?P<kind>read-only property|constant)",
    re.IGNORECASE
)

class TSReadonlyAssignmentRule(BaseDiagnosticRule):
    """Diagnoses TypeScript assignments to immutable constants or readonly properties (TS2540, TS2588)."""

    rule_id = "ts-readonly-assignment"
    name = "TypeScript Readonly/Constant Assignment"
    category = "types"
    priority = 84

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = TS_READONLY_ASSIGNMENT_REGEX.search(cleaned_output)
        if match:
            code = match.group("code")
            target = match.group("target")
            kind = match.group("kind")
            raw_err = match.group(0).strip()

            title = f"💀 Cannot assign to '{target}' because it is a {kind} (TS{code})"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "code": code,
                    "target": target,
                    "kind": kind,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        target = vars.get("target", "target")
        kind = vars.get("kind", "constant")

        if "read-only" in kind.lower():
            return (
                f"Property '{target}' is marked with the 'readonly' modifier in its interface or class definition, "
                f"so it cannot be reassigned after object creation."
            )

        return (
            f"Variable '{target}' was declared with 'const' and cannot be reassigned. "
            f"Only variables declared with 'let' or 'var' can be reassigned."
        )

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        target = vars.get("target", "target")
        kind = vars.get("kind", "constant")

        if "read-only" in kind.lower():
            return [
                f"Remove the 'readonly' modifier from property '{target}' in the type definition if mutation is intended.",
                f"Initialize property '{target}' during object instantiation or inside the class constructor.",
                f"Create a new object with the updated property value instead of mutating in place."
            ]

        return [
            f"Change the variable declaration from `const {target}` to `let {target}` if you need to reassign it.",
            f"Declare a new distinct variable rather than reassigning '{target}'.",
            f"If mutating an object or array declared with const, mutate its properties rather than reassigning the variable itself."
        ]
