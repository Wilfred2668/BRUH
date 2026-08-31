"""Diagnostic rule for dictionary KeyError lookups."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

KEY_ERR_REGEX = re.compile(
    r"^KeyError:\s*(?:['\"](?P<key1>[^'\"]+)['\"]|(?P<key2>[^\r\n]+))",
    re.MULTILINE | re.IGNORECASE
)

class KeyErrorRule(BaseDiagnosticRule):
    """Diagnoses missing key lookups in Python dictionaries."""

    rule_id = "key-error"
    name = "KeyError"
    category = "runtime"
    priority = 76

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = KEY_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            key_name = match.group("key1") or match.group("key2") or "key"
            key_name = key_name.strip()

            return RuleMatch(
                matched=True,
                title=f"💀 KeyError: '{key_name}'",
                original_error=raw_err,
                extracted_vars={"key": key_name, "raw": raw_err}
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        key = vars.get("key", "key")
        return f"Python tried to access the key '{key}' in a dictionary, but that key does not exist."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        key = vars.get("key", "key")
        return [
            f"Check if the dictionary key '{key}' is misspelled or has different casing.",
            f"Use dict.get('{key}', default) to provide a fallback value instead of raising an error.",
            f"Verify dictionary contents with print() or `if '{key}' in dict:` before accessing."
        ]
