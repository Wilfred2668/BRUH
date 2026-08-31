"""Diagnostic rule for TypeScript element implicit any indexing errors (TS7053)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_ELEMENT_IMPLICIT_ANY_REGEX = re.compile(
    r"error\s+TS7053:\s*Element implicitly has an\s+'any'\s+type because (?:type\s+'(?P<target_type1>[^']+)'\s+has no index signature|expression of type\s+'(?P<index_type>[^']+)'\s+can't be used to index type\s+'(?P<target_type2>[^']+)')",
    re.IGNORECASE
)

class TSElementImplicitAnyRule(BaseDiagnosticRule):
    """Diagnoses TypeScript dynamic indexing errors on objects without index signatures (TS7053)."""

    rule_id = "ts-element-implicit-any"
    name = "TypeScript Element Implicit Any"
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

        match = TS_ELEMENT_IMPLICIT_ANY_REGEX.search(cleaned_output)
        if match:
            target_type = match.group("target_type2") or match.group("target_type1") or "object"
            index_type = match.group("index_type") or "string"
            raw_err = match.group(0).strip()

            title = f"💀 Element implicitly has an 'any' type on '{target_type}' (TS7053)"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "target_type": target_type,
                    "index_type": index_type,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        target_type = vars.get("target_type", "type")
        index_type = vars.get("index_type", "string")
        return (
            f"You are dynamically accessing a property using a key of type '{index_type}' on type '{target_type}', "
            f"but '{target_type}' does not define an index signature permitting arbitrary indexing."
        )

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        target_type = vars.get("target_type", "type")

        return [
            "Use a keyof type assertion when indexing: `obj[key as keyof typeof obj]` or `obj[key as keyof MyInterface]`.",
            f"Add an index signature to '{target_type}': `[key: string]: string;` or type the object as `Record<string, unknown>`.",
            "If the key comes from a fixed set of property names, type the key variable with a string literal union (e.g. `'name' | 'age'`)."
        ]
