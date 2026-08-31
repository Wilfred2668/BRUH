"""Diagnostic rule for TypeScript missing required property errors (TS2741, TS2739)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_SINGLE_MISSING_PROP_REGEX = re.compile(
    r"error\s+TS2741:\s*Property\s+'(?P<prop>[^']+)'\s+is missing in type\s+'(?P<source>[^']+)'\s+but required in type\s+'(?P<target>[^']+)'",
    re.IGNORECASE
)

TS_MULTI_MISSING_PROP_REGEX = re.compile(
    r"error\s+TS2739:\s*Type\s+'(?P<source>[^']+)'\s+is missing the following properties from type\s+'(?P<target>[^']+)':\s*(?P<props>[^\r\n]+)",
    re.IGNORECASE
)

class TSMissingRequiredPropertyRule(BaseDiagnosticRule):
    """Diagnoses TypeScript missing required property errors on object literals and assignments (TS2741, TS2739)."""

    rule_id = "ts-missing-required-property"
    name = "TypeScript Missing Required Property"
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

        # 1. Single missing property (TS2741)
        m_single = TS_SINGLE_MISSING_PROP_REGEX.search(cleaned_output)
        if m_single:
            prop = m_single.group("prop")
            source = m_single.group("source")
            target = m_single.group("target")
            raw_err = m_single.group(0).strip()

            title = f"💀 Property '{prop}' is missing in type '{source}' (required in '{target}') (TS2741)"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "prop": prop,
                    "source": source,
                    "target": target,
                    "is_multi": False,
                    "raw": raw_err
                }
            )

        # 2. Multiple missing properties (TS2739)
        m_multi = TS_MULTI_MISSING_PROP_REGEX.search(cleaned_output)
        if m_multi:
            source = m_multi.group("source")
            target = m_multi.group("target")
            props = m_multi.group("props").strip()
            raw_err = m_multi.group(0).strip()

            title = f"💀 Missing required properties from '{target}': {props} (TS2739)"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "source": source,
                    "target": target,
                    "props": props,
                    "is_multi": True,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        target = vars.get("target", "target type")
        is_multi = vars.get("is_multi", False)

        if is_multi:
            props = vars.get("props", "required properties")
            return f"The object value is missing required properties ({props}) defined in interface/type '{target}'."

        prop = vars.get("prop", "property")
        return f"Property '{prop}' is declared as a required field in type '{target}', but is not provided in your object definition."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        target = vars.get("target", "type")
        is_multi = vars.get("is_multi", False)

        if is_multi:
            props = vars.get("props", "required fields")
            return [
                f"Add the missing properties ({props}) to your object literal.",
                f"If any of these fields are optional in '{target}', mark them with `?` in the interface definition.",
                f"If constructing the object dynamically in steps, use `Partial<{target}>` during initialization."
            ]

        prop = vars.get("prop", "property")
        return [
            f"Add property '{prop}' with an appropriate value to your object literal.",
            f"If '{prop}' is not always mandatory, make it optional in '{target}': `{prop}?: ...`.",
            f"If initializing an empty object, type as `Partial<{target}>` or use a factory function."
        ]
