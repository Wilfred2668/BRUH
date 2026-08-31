"""Diagnostic rule for JavaScript / Node.js ReferenceError."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

JS_REF_ERR_REGEX = re.compile(
    r"(?:ReferenceError:\s*(?P<var>[a-zA-Z_$][a-zA-Z0-9_$]*)\s*is not defined|"
    r"ReferenceError:\s*Cannot access '(?P<var2>[a-zA-Z_$][a-zA-Z0-9_$]*)' before initialization)",
    re.IGNORECASE
)

class JSReferenceErrorRule(BaseDiagnosticRule):
    """Diagnoses undefined variables and scope errors in JavaScript / Node.js."""

    rule_id = "js-reference-error"
    name = "JavaScript ReferenceError"
    category = "runtime"
    priority = 78

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = JS_REF_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            var_name = match.group("var") or match.group("var2")
            is_tdz = "before initialization" in raw_err.lower()

            if is_tdz and var_name:
                title = f"💀 ReferenceError: Cannot access '{var_name}' before initialization"
            elif var_name:
                title = f"💀 ReferenceError: '{var_name}' is not defined"
            else:
                title = "💀 JavaScript ReferenceError"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "var_name": var_name,
                    "is_tdz": is_tdz,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        var_name = vars.get("var_name")
        is_tdz = vars.get("is_tdz")

        if is_tdz and var_name:
            return (
                f"JavaScript attempted to access '{var_name}' before its declaration was reached. "
                f"Variables declared with 'let' or 'const' cannot be read before their definition (Temporal Dead Zone)."
            )
        elif var_name:
            return (
                f"JavaScript attempted to access the identifier '{var_name}', but it has not been "
                f"declared in the current scope or imported from another module."
            )

        return "JavaScript attempted to access a variable or identifier that is not defined in the active scope."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        var_name = vars.get("var_name")
        is_tdz = vars.get("is_tdz")

        if is_tdz and var_name:
            return [
                f"Move the declaration `let {var_name} = ...` or `const {var_name} = ...` above the line where it is first used.",
                f"Ensure you are not referencing `{var_name}` inside its own initializer."
            ]

        suggestions = []
        if var_name:
            suggestions.append(f"Check for typos in the variable name '{var_name}'.")
            suggestions.append(f"Declare the variable using `const {var_name} = ...` or `let {var_name} = ...` before using it.")
            suggestions.append(f"If '{var_name}' is from an external file or npm package, add the missing `import` or `require`.")
        else:
            suggestions.append("Check the line indicated in the stack trace for undeclared variable names.")

        return suggestions
