"""Diagnostic rule for IndexError out-of-range sequence access."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

INDEX_ERR_REGEX = re.compile(
    r"^IndexError:\s*(?P<msg>list index out of range|string index out of range|tuple index out of range|pop from empty (?:list|tuple)|index out of range)",
    re.MULTILINE | re.IGNORECASE
)

class IndexErrorRule(BaseDiagnosticRule):
    """Diagnoses out-of-bounds indexing on lists, strings, and tuples."""

    rule_id = "index-error"
    name = "IndexError"
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

        match = INDEX_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            msg = match.group("msg") or "index out of range"

            return RuleMatch(
                matched=True,
                title=f"💀 IndexError: {msg}",
                original_error=raw_err,
                extracted_vars={"msg": msg, "raw": raw_err}
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        msg = vars.get("msg", "index out of range")
        if "empty" in msg.lower():
            return "Your code tried to pop or access an item from a list or tuple that is currently empty."
        return "Your code tried to access an item at an index that does not exist in the list or sequence (the sequence is shorter than the index requested)."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        return [
            "Remember that indexing is 0-based (e.g. a list with 3 elements has valid indices 0, 1, and 2).",
            "Check the length of the list using `len(sequence)` before accessing it.",
            "Ensure the sequence is not empty before indexing or removing elements."
        ]
