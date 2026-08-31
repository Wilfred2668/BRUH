"""Diagnostic rule for undefined variable NameError and ReferenceError."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

NAME_ERR_REGEX = re.compile(
    r"(?:(?:NameError:\s*name ['\"](?P<py_name>[^'\"]+)['\"]\s*is not defined)|"
    r"(?:UnboundLocalError:\s*cannot access local variable ['\"](?P<unbound_name1>[^'\"]+)['\"])|"
    r"(?:UnboundLocalError:\s*local variable ['\"](?P<unbound_name2>[^'\"]+)['\"]\s*referenced before assignment)|"
    r"(?:ReferenceError:\s*(?P<js_name>[a-zA-Z0-9_$]+)\s*is not defined))",
    re.IGNORECASE
)

class NameErrorRule(BaseDiagnosticRule):
    """Diagnoses undefined variable lookups in Python (NameError) and Node.js (ReferenceError)."""

    rule_id = "name-error"
    name = "NameError / Undefined Variable"
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

        match = NAME_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            py_name = match.group("py_name")
            unbound = match.group("unbound_name1") or match.group("unbound_name2")
            js_name = match.group("js_name")

            if py_name:
                title = f"💀 NameError: name '{py_name}' is not defined"
                name_var = py_name
                kind = "name"
            elif unbound:
                title = f"💀 UnboundLocalError: local variable '{unbound}' referenced before assignment"
                name_var = unbound
                kind = "unbound"
            else:
                title = f"💀 ReferenceError: {js_name} is not defined"
                name_var = js_name
                kind = "reference"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "name": name_var,
                    "kind": kind,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        name = vars.get("name", "variable")
        kind = vars.get("kind", "name")

        if kind == "unbound":
            return f"Your code referenced the local variable '{name}' before assigning a value to it in the current scope."
        elif kind == "reference":
            return f"JavaScript encountered the identifier '{name}', but no variable, function, or import with that name exists in this scope."
        
        return f"Your code used the variable or function '{name}', but it hasn't been defined, initialized, or imported in this scope."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        name = vars.get("name", "variable")
        kind = vars.get("kind", "name")

        if kind == "unbound":
            return [
                f"Initialize '{name}' before referencing it inside the function.",
                f"If you intended to modify a global variable, add `global {name}` at the top of the function.",
                "Check for nested conditional blocks where the variable assignment was skipped."
            ]

        return [
            f"Check for spelling or capitalization typos in '{name}'.",
            f"Ensure '{name}' is defined or imported before the line where it is used.",
            f"Check variable scope if '{name}' was declared inside a function or loop."
        ]
