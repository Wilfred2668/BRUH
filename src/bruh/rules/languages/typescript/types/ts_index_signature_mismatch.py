"""Diagnostic rule for TypeScript index signature mismatch errors (TS2411)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_INDEX_SIG_MISMATCH_REGEX = re.compile(
    r"error\s+TS2411:\s*Property\s+'(?P<prop>[^']+)'\s+of type\s+'(?P<prop_type>[^']+)'\s+is not assignable to\s+'(?P<index_key_type>[^']+)'\s+index type\s+'(?P<index_val_type>[^']+)'",
    re.IGNORECASE
)

class TSIndexSignatureMismatchRule(BaseDiagnosticRule):
    """Diagnoses TypeScript property types that conflict with declared index signatures (TS2411)."""

    rule_id = "ts-index-signature-mismatch"
    name = "TypeScript Index Signature Mismatch"
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

        match = TS_INDEX_SIG_MISMATCH_REGEX.search(cleaned_output)
        if match:
            prop = match.group("prop")
            prop_type = match.group("prop_type")
            index_key_type = match.group("index_key_type")
            index_val_type = match.group("index_val_type")
            raw_err = match.group(0).strip()

            title = f"💀 Property '{prop}' incompatible with '{index_key_type}' index type '{index_val_type}' (TS2411)"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "prop": prop,
                    "prop_type": prop_type,
                    "index_key_type": index_key_type,
                    "index_val_type": index_val_type,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        prop = vars.get("prop", "property")
        prop_type = vars.get("prop_type", "type")
        index_val_type = vars.get("index_val_type", "index type")
        return (
            f"TypeScript index signatures enforce that all named properties in a type must be assignable "
            f"to the index signature's return type. Property '{prop}' has type '{prop_type}', which does not match '{index_val_type}'."
        )

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        prop = vars.get("prop", "property")
        prop_type = vars.get("prop_type", "type")
        index_val_type = vars.get("index_val_type", "index type")

        return [
            f"Widen the index signature return type to include '{prop_type}': e.g. `[key: string]: {index_val_type} | {prop_type};`.",
            f"Change the type of property '{prop}' to '{index_val_type}' so it conforms to the index signature.",
            "Separate the indexed dictionary mapping and the fixed named properties into two distinct interfaces or nested objects."
        ]
