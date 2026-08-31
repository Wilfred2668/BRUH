"""Diagnostic rule for NoneType and undefined property access errors."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

ATTR_ERR_REGEX = re.compile(
    r"(?:(?:AttributeError:\s*(?:'|type object '|module ')?(?P<py_type>[^']+)'?\s*(?:object )?has no attribute\s*'(?P<py_attr>[^']+)'(?:\.\s*Did you mean:\s*['\"](?P<did_mean>[^'\"]+)['\"])?)|"
    r"(?:TypeError:\s*Cannot read propert(?:y|ies) of (?P<js_null>undefined|null)(?:\s*\(reading\s*'(?P<js_attr>[^']+)'\))?)|"
    r"(?:TypeError:\s*'(?P<unsub_type>[^']+)' object is not subscriptable))",
    re.IGNORECASE
)

class RuntimeAttributeErrorRule(BaseDiagnosticRule):
    """Diagnoses NoneType attribute errors, module/class missing attributes, and undefined/null property lookups."""

    rule_id = "runtime-attribute-error"
    name = "Runtime Attribute / Property Error"
    category = "runtime"
    priority = 72

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = ATTR_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            py_type = match.group("py_type")
            py_attr = match.group("py_attr")
            did_mean = match.group("did_mean")
            js_null = match.group("js_null")
            js_attr = match.group("js_attr")
            unsub = match.group("unsub_type")

            if py_type:
                title = f"💀 AttributeError: {py_type} has no attribute '{py_attr}'"
            elif js_null:
                attr_str = f" '{js_attr}'" if js_attr else ""
                title = f"💀 TypeError: Cannot read property{attr_str} of {js_null}"
            elif unsub:
                title = f"💀 TypeError: {unsub} is not subscriptable"
            else:
                title = "💀 Runtime Type Error"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "py_type": py_type,
                    "py_attr": py_attr,
                    "did_mean": did_mean,
                    "js_null": js_null,
                    "js_attr": js_attr,
                    "unsub_type": unsub,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        py_type = vars.get("py_type")
        py_attr = vars.get("py_attr")
        js_null = vars.get("js_null")
        js_attr = vars.get("js_attr")
        unsub = vars.get("unsub_type")

        if py_type == "NoneType":
            return f"Your code expected an object, but received None instead when trying to access '{py_attr}'."
        if py_type:
            return f"The object or module '{py_type}' does not have an attribute, property, or method named '{py_attr}'."
        if js_null:
            attr_str = f" '{js_attr}'" if js_attr else " a property"
            return f"Your code tried to access{attr_str} on a variable that is currently {js_null}."
        if unsub:
            return f"You used square brackets `[ ]` on an object of type '{unsub}', which cannot be indexed like a list or dictionary."
        return "A variable had an unexpected type or value when accessed."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        py_type = vars.get("py_type")
        py_attr = vars.get("py_attr")
        did_mean = vars.get("did_mean")
        js_null = vars.get("js_null")
        js_attr = vars.get("js_attr")

        if did_mean:
            return [
                f"Did you mean to use '{did_mean}' instead of '{py_attr}'?",
                f"Check for spelling or capitalization typos in '{py_attr}'.",
                f"Inspect available attributes using `dir({py_type})`."
            ]

        # Common cross-language mistakes (e.g. .length, .lenght, .size on Python lists/dicts)
        if py_attr and py_attr.lower() in ("length", "lenght", "size") and py_type and py_type.lower() in ("list", "dict", "str", "tuple", "set"):
            return [
                f"To get the length of a {py_type} in Python, use the built-in function `len(x)` instead of `.{py_attr}()`.",
                f"Check for typos if you intended to call another method on '{py_type}'.",
                f"Inspect available methods on this object using `dir({py_type})`."
            ]

        if py_type == "NoneType":
            return [
                "Check where the variable was created or returned before this line.",
                f"Add a check (`if variable is not None:`) before accessing '{py_attr}'.",
                "Verify that your function or API call returned real data instead of None."
            ]
        if js_null:
            attr_str = f".{js_attr}" if js_attr else ""
            return [
                "Check where the variable was assigned before this line.",
                f"Use optional chaining (`variable?{attr_str}`) or check if it exists before accessing it.",
                "Verify that your API response or async function returned data."
            ]
        return [
            f"Check if '{py_attr}' is spelled correctly or if the method name changed.",
            "Verify the type and available attributes using `dir(object)` or `print(type(object))`.",
            "Make sure you didn't shadow a standard library module with a local file of the same name."
        ]
