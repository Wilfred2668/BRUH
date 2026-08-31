"""Diagnostic rule for Python ImportError (cannot import name, circular imports)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

IMPORT_ERR_REGEX = re.compile(
    r"(?:(?:ImportError:\s*cannot import name ['\"](?P<attr>[^'\"]+)['\"]\s*from\s*(?:partially initialized module )?['\"](?P<mod>[^'\"]+)['\"](?:\s*\(most likely due to a circular import\))?)|"
    r"(?:ImportError:\s*cannot import name ['\"](?P<attr2>[^'\"]+)['\"]))",
    re.IGNORECASE
)

class ImportErrorRule(BaseDiagnosticRule):
    """Diagnoses missing attributes inside installed modules, circular imports, and namespace shadowing."""

    rule_id = "import-error"
    name = "ImportError"
    category = "dependency"
    priority = 89

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        # Do not steal ModuleNotFoundError (handled by ModuleNotFoundRule with priority 90)
        if "modulenotfounderror" in cleaned_output.lower() or "no module named" in cleaned_output.lower():
            return None

        match = IMPORT_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            attr = match.group("attr") or match.group("attr2") or "object"
            mod = match.group("mod")
            is_circular = "circular import" in cleaned_output.lower()

            if is_circular and mod:
                title = f"💀 Circular Import: cannot import '{attr}' from '{mod}'"
            elif mod:
                title = f"💀 ImportError: cannot import '{attr}' from '{mod}'"
            else:
                title = f"💀 ImportError: cannot import name '{attr}'"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "attr": attr,
                    "mod": mod,
                    "is_circular": is_circular,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        attr = vars.get("attr", "name")
        mod = vars.get("mod")
        is_circular = vars.get("is_circular")

        if is_circular and mod:
            return f"A circular import occurred because your code and '{mod}' are trying to import from each other before either module has finished loading."
        elif mod:
            return f"Python located the module '{mod}', but '{attr}' does not exist inside it (or the module was shadowed by a local file with the same name)."

        return f"Python was unable to import the name '{attr}'."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        attr = vars.get("attr", "name")
        mod = vars.get("mod")
        is_circular = vars.get("is_circular")

        if is_circular:
            return [
                "Refactor the imports so modules do not depend on each other at top-level.",
                "Move the import inside the specific function that uses it instead of at the top of the file.",
                "Combine tightly coupled classes/functions into the same module."
            ]

        mod_str = f" in '{mod}'" if mod else ""
        return [
            f"Check if you have a local file or folder named '{mod}.py' shadowing the real library.",
            f"Verify the spelling and capitalization of '{attr}'{mod_str}.",
            f"Check the documentation for '{mod}' to confirm that '{attr}' is exported in this version."
        ]
