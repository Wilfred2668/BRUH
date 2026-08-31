"""Diagnostic rule for TypeScript type mismatch errors (TS2322, TS2345)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_TYPE_MISMATCH_REGEX = re.compile(
    r"(?:error\s+TS2322:\s*Type\s+'(?P<source>[^']+)'\s+is not assignable to type\s+'(?P<target>[^']+)'|"
    r"error\s+TS2345:\s*Argument of type\s+'(?P<arg_source>[^']+)'\s+is not assignable to parameter of type\s+'(?P<arg_target>[^']+)')",
    re.IGNORECASE
)

class TSTypeMismatchRule(BaseDiagnosticRule):
    """Diagnoses TypeScript variable and parameter type mismatch errors (TS2322, TS2345)."""

    rule_id = "ts-type-mismatch"
    name = "TypeScript Type Mismatch"
    category = "types"
    priority = 79

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = TS_TYPE_MISMATCH_REGEX.search(cleaned_output)
        if match:
            source = match.group("source") or match.group("arg_source")
            target = match.group("target") or match.group("arg_target")
            is_arg = bool(match.group("arg_source"))

            raw_err = match.group(0).strip()
            if is_arg:
                title = f"💀 Type Mismatch: '{source}' is not assignable to parameter '{target}' (TS2345)"
            else:
                title = f"💀 Type Mismatch: Type '{source}' is not assignable to type '{target}' (TS2322)"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "source": source,
                    "target": target,
                    "is_arg": is_arg,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        source = vars.get("source", "value")
        target = vars.get("target", "target")
        is_arg = vars.get("is_arg", False)

        if is_arg:
            return (
                f"The function parameter requires a value of type '{target}', "
                f"but an argument of incompatible type '{source}' was passed."
            )

        return (
            f"The variable or property is typed as '{target}', "
            f"but you assigned a value of type '{source}'."
        )

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        source = vars.get("source", "value")
        target = vars.get("target", "target")
        is_arg = vars.get("is_arg", False)

        if is_arg:
            return [
                f"Convert or pass an argument matching type '{target}'.",
                f"Update the function parameter declaration if '{source}' should also be accepted: `({target} | {source})`.",
                "Use a type guard or explicit type assertion (e.g. `as unknown as ...`) only if you are certain the value satisfies the runtime contract."
            ]

        return [
            f"Change the assigned value so that it conforms to type '{target}'.",
            f"Update the variable type annotation to allow '{source}' (e.g. `{target} | {source}`).",
            f"Explicitly convert the value from '{source}' to '{target}' before assignment."
        ]
