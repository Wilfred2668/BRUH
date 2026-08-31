"""Diagnostic rule for TypeScript possibly null or undefined errors (TS2531, TS2532, TS2533, TS18047, TS18048)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_NULL_UNDEFINED_REGEX = re.compile(
    r"error\s+TS(?P<code>2531|2532|2533|18047|18048):\s*(?:Object\s+is\s+possibly\s+'(?P<kind1>null|undefined|null\' or \'undefined)'|'(?P<target>[^']+)'\s+is\s+possibly\s+'(?P<kind2>null|undefined)')",
    re.IGNORECASE
)

class TSNullUndefinedRule(BaseDiagnosticRule):
    """Diagnoses TypeScript strict null check errors on nullable objects and variables."""

    rule_id = "ts-null-undefined"
    name = "TypeScript Null/Undefined Access"
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

        match = TS_NULL_UNDEFINED_REGEX.search(cleaned_output)
        if match:
            code = match.group("code")
            kind = match.group("kind2") or match.group("kind1") or "null/undefined"
            target = match.group("target")
            raw_err = match.group(0).strip()

            if target:
                title = f"💀 '{target}' is possibly '{kind}' (TS{code})"
            else:
                title = f"💀 Object is possibly '{kind}' (TS{code})"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "code": code,
                    "kind": kind,
                    "target": target,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        target = vars.get("target")
        kind = vars.get("kind", "null/undefined")

        if target:
            return (
                f"Under strictNullChecks, variable '{target}' may be '{kind}' at this point in execution, "
                f"so directly accessing its properties or calling it risks a runtime error."
            )

        return (
            f"Under strictNullChecks, the object operand is typed to include '{kind}', "
            f"so directly reading properties or calling methods without a guard is unsafe."
        )

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        target = vars.get("target", "object")

        return [
            f"Use optional chaining when accessing properties: `{target}?.property` or `{target}?.method()`.",
            f"Add a null/undefined check before use: `if ({target} != null) {{ ... }}` or `if (!{target}) return;`.",
            f"If you are certain the value is never null at runtime, use non-null assertion: `{target}!` or a fallback value `{target} ?? defaultValue`."
        ]
