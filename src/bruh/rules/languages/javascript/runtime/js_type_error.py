"""Diagnostic rule for JavaScript / Node.js TypeError."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

JS_TYPE_ERR_REGEX = re.compile(
    r"(?:(?:TypeError:\s*Cannot read propert(?:y|ies) of (?P<base1>undefined|null)\s*(?:\(reading '(?P<prop1>[^']+)'\)|'(?P<prop1_alt>[^']+)'))|"
    r"(?:TypeError:\s*Cannot set propert(?:y|ies) of (?P<base2>undefined|null)\s*(?:\(setting '(?P<prop2>[^']+)'\)|'(?P<prop2_alt>[^']+)'))|"
    r"(?:TypeError:\s*(?P<fn_name>[a-zA-Z0-9_$.]+)\s*is not a function)|"
    r"(?:TypeError:\s*Cannot convert (?P<conv_base>undefined or null|object) to object)|"
    r"(?:TypeError:\s*Assignment to constant variable\.?))",
    re.IGNORECASE
)

class JSTypeErrorRule(BaseDiagnosticRule):
    """Diagnoses type errors, null/undefined property lookups, and non-function invocations in JavaScript."""

    rule_id = "js-type-error"
    name = "JavaScript TypeError"
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

        match = JS_TYPE_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            base1 = match.group("base1")
            prop1 = match.group("prop1") or match.group("prop1_alt")
            base2 = match.group("base2")
            prop2 = match.group("prop2") or match.group("prop2_alt")
            fn_name = match.group("fn_name")
            is_const = "assignment to constant" in raw_err.lower()
            is_convert = "cannot convert" in raw_err.lower()

            if prop1 and base1:
                title = f"💀 TypeError: Cannot read property '{prop1}' of {base1}"
            elif prop2 and base2:
                title = f"💀 TypeError: Cannot set property '{prop2}' on {base2}"
            elif fn_name:
                title = f"💀 TypeError: '{fn_name}' is not a function"
            elif is_const:
                title = "💀 TypeError: Assignment to constant variable"
            elif is_convert:
                title = "💀 TypeError: Cannot convert null/undefined to object"
            else:
                title = "💀 JavaScript TypeError"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "base1": base1,
                    "prop1": prop1,
                    "base2": base2,
                    "prop2": prop2,
                    "fn_name": fn_name,
                    "is_const": is_const,
                    "is_convert": is_convert,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        prop1 = vars.get("prop1")
        base1 = vars.get("base1")
        prop2 = vars.get("prop2")
        base2 = vars.get("base2")
        fn_name = vars.get("fn_name")
        is_const = vars.get("is_const")

        if prop1 and base1:
            return (
                f"Your code tried to access the property '{prop1}', but the target object evaluated to "
                f"'{base1}' instead of a valid object."
            )
        elif prop2 and base2:
            return (
                f"Your code tried to assign a value to property '{prop2}', but the parent object is '{base2}'."
            )
        elif fn_name:
            return (
                f"Your code attempted to call '{fn_name}()' as a function, but '{fn_name}' is "
                f"undefined, null, or a non-function value."
            )
        elif is_const:
            return "Your code attempted to reassign a variable that was declared with 'const'."

        return "JavaScript encountered an operation on a value of an incompatible or invalid type."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        prop1 = vars.get("prop1")
        prop2 = vars.get("prop2")
        fn_name = vars.get("fn_name")
        is_const = vars.get("is_const")

        if prop1:
            return [
                f"Use optional chaining (`?.`) to safely access the property: e.g. `obj?.{prop1}`.",
                "Verify the object is populated (e.g. check API responses or function return values).",
                f"Add a guard clause: `if (obj && obj.{prop1}) {{ ... }}`."
            ]
        elif prop2:
            return [
                "Initialize the parent object before assigning properties to it: `const obj = {};`.",
                "Check whether the variable holding the object was overwritten with null or undefined."
            ]
        elif fn_name:
            return [
                f"Check that '{fn_name}' is properly defined and imported before calling it.",
                f"Ensure you did not overwrite '{fn_name}' with a non-function value (e.g. an object or string).",
                f"If '{fn_name}' is an asynchronous method, ensure you awaited the parent object first."
            ]
        elif is_const:
            return [
                "Change the variable declaration from `const` to `let` if you intend to reassign it.",
                "If mutating an object or array, modify its properties/elements instead of reassigning the variable."
            ]

        return [
            "Check the stack trace location to inspect the variables involved in the failing expression.",
            "Log variable values using `console.log()` before the failing line to inspect their runtime types."
        ]
