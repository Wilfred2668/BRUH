"""Diagnostic rule for TypeScript implicit any errors (TS7006, TS7005, TS7008, TS7034)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_IMPLICIT_ANY_REGEX = re.compile(
    r"error\s+TS(?P<code>7006|7005|7008|7034):\s*(?:(?P<target>Parameter|Variable|Member)\s+'(?P<name>[^']+)'\s+implicitly has an?\s+'(?P<type>any|any\[\])'\s+type|"
    r"Variable\s+'(?P<name2>[^']+)'\s+implicitly has type\s+'(?P<type2>any)'\s+in some locations)",
    re.IGNORECASE
)

class TSImplicitAnyRule(BaseDiagnosticRule):
    """Diagnoses TypeScript implicit any errors when noImplicitAny is enabled (TS7006, TS7005, TS7008, TS7034)."""

    rule_id = "ts-implicit-any"
    name = "TypeScript Implicit Any"
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

        match = TS_IMPLICIT_ANY_REGEX.search(cleaned_output)
        if match:
            code = match.group("code") or "7006"
            target = match.group("target") or "Variable"
            name = match.group("name") or match.group("name2")
            any_type = match.group("type") or match.group("type2") or "any"
            raw_err = match.group(0).strip()

            title = f"💀 {target} '{name}' implicitly has an '{any_type}' type (TS{code})"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "code": code,
                    "target": target,
                    "name": name,
                    "any_type": any_type,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        target = vars.get("target", "Parameter").lower()
        name = vars.get("name", "variable")
        any_type = vars.get("any_type", "any")

        if target == "member":
            return (
                f"Class property/member '{name}' was declared without a type annotation or initializer, "
                f"causing TypeScript to infer '{any_type}' which is disallowed under 'noImplicitAny'."
            )
        elif target == "parameter":
            return (
                f"Function parameter '{name}' has no type annotation or default value, "
                f"causing TypeScript to infer '{any_type}' which violates compiler option 'noImplicitAny'."
            )

        return (
            f"Variable '{name}' was declared without an initializer or type annotation, "
            f"so TypeScript cannot determine its type and forbids falling back to '{any_type}' silently."
        )

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        target = vars.get("target", "Parameter").lower()
        name = vars.get("name", "variable")

        if target == "member":
            return [
                f"Add an explicit type annotation to the class member: `{name}: string;` or `{name}: number;`.",
                f"Initialize the member with a default value: `{name} = ''` or in the class `constructor()`.",
                f"If the member can hold various types, annotate as a union: `{name}: string | null;`."
            ]
        elif target == "parameter":
            return [
                f"Add an explicit type annotation: `{name}: string`, `{name}: number`, or custom interface/type.",
                f"Provide a default argument value: `function fn({name} = defaultValue)`.",
                f"If dynamic typing is intended, annotate explicitly: `{name}: unknown` or `{name}: any`."
            ]

        return [
            f"Initialize the variable when declared: `let {name} = ...`.",
            f"Add an explicit type annotation: `let {name}: string;` or `let {name}: MyType;`.",
            f"If {name} can be undefined initially, annotate as union: `let {name}: string | undefined;`."
        ]
