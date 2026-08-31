"""Diagnostic rule for common TypeError and function signature mismatch errors."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TYPE_ERR_REGEX = re.compile(
    r"(?:(?:TypeError:\s*unsupported operand type\(s\) for (?P<op>[^:]+):\s*'(?P<t1>[^']+)' and '(?P<t2>[^']+)')|"
    r"(?:TypeError:\s*can only concatenate str \(not \"(?P<cat_t>[^\"]+)\"\) to str)|"
    r"(?:TypeError:\s*(?P<fn1>[a-zA-Z0-9_\.]+\(\))\s*takes (?P<exp>\d+) positional argument(?:s)? but (?P<act>\d+) (?:was|were) given)|"
    r"(?:TypeError:\s*(?P<fn2>[a-zA-Z0-9_\.]+\(\))\s*missing (?P<missing_cnt>\d+) required positional argument(?:s)?:\s*'(?P<missing_arg>[^']+)')|"
    r"(?:TypeError:\s*'(?P<not_call>[^']+)' object is not callable)|"
    r"(?:TypeError:\s*(?P<js_fn>[a-zA-Z0-9_$\.]+)\s*is not a function))",
    re.IGNORECASE
)

class TypeErrorRule(BaseDiagnosticRule):
    """Diagnoses type mismatches, argument count errors, and non-callable invocations."""

    rule_id = "type-error"
    name = "TypeError"
    category = "runtime"
    priority = 74

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        # Do not steal attribute errors that were specifically handled by RuntimeAttributeErrorRule
        if "cannot read propert" in cleaned_output.lower() or "is not subscriptable" in cleaned_output.lower():
            return None

        match = TYPE_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            op = match.group("op")
            t1 = match.group("t1")
            t2 = match.group("t2")
            cat_t = match.group("cat_t")
            fn1 = match.group("fn1")
            exp = match.group("exp")
            act = match.group("act")
            fn2 = match.group("fn2")
            missing_arg = match.group("missing_arg")
            not_call = match.group("not_call")
            js_fn = match.group("js_fn")

            if op and t1 and t2:
                title = f"💀 TypeError: unsupported operand for {op} ('{t1}' and '{t2}')"
                kind = "operand"
            elif cat_t:
                title = f"💀 TypeError: cannot concatenate '{cat_t}' to str"
                kind = "concat"
            elif fn1:
                title = f"💀 TypeError: {fn1} argument count mismatch"
                kind = "arg_count"
            elif fn2 and missing_arg:
                title = f"💀 TypeError: {fn2} missing argument '{missing_arg}'"
                kind = "missing_arg"
            elif not_call:
                title = f"💀 TypeError: '{not_call}' is not callable"
                kind = "not_callable"
            elif js_fn:
                title = f"💀 TypeError: {js_fn} is not a function"
                kind = "not_function"
            else:
                title = "💀 TypeError: Type Mismatch"
                kind = "generic"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "kind": kind,
                    "op": op,
                    "t1": t1,
                    "t2": t2,
                    "cat_t": cat_t,
                    "fn": fn1 or fn2,
                    "exp": exp,
                    "act": act,
                    "missing_arg": missing_arg,
                    "not_call": not_call,
                    "js_fn": js_fn,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        kind = vars.get("kind", "generic")

        if kind == "operand":
            return f"You tried to apply operator '{vars.get('op')}' between incompatible types: '{vars.get('t1')}' and '{vars.get('t2')}'."
        elif kind == "concat":
            return f"Python cannot concatenate a '{vars.get('cat_t')}' directly to a string with `+`. You must convert it to a string first."
        elif kind == "arg_count":
            return f"The function {vars.get('fn')} expects {vars.get('exp')} positional argument(s), but received {vars.get('act')}."
        elif kind == "missing_arg":
            return f"The function {vars.get('fn')} was called without the required positional argument '{vars.get('missing_arg')}'."
        elif kind == "not_callable":
            return f"Your code tried to call a '{vars.get('not_call')}' object as if it were a function using parentheses `()`."
        elif kind == "not_function":
            return f"JavaScript tried to invoke '{vars.get('js_fn')}' as a function, but its value is undefined or not a callable function."

        return "An operation or function call was applied to an object of an inappropriate type."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        kind = vars.get("kind", "generic")

        if kind in ("operand", "concat"):
            return [
                "Convert the value explicitly using `str(...)`, `int(...)`, or formatted strings (f-strings).",
                "Check the data types of variables being combined with `type(var)`.",
                "Ensure variables contain the expected numeric or string types before operating on them."
            ]
        elif kind in ("arg_count", "missing_arg"):
            return [
                "Check the function definition to see the expected parameter list.",
                "Verify that all required arguments are passed when calling the function.",
                "If calling a method on a class, ensure `self` is included as the first parameter."
            ]
        elif kind in ("not_callable", "not_function"):
            return [
                "Check if you accidentally shadowed a function name with a variable of the same name.",
                "Remove trailing parentheses `()` if you intended to pass the variable/property rather than call it.",
                "Make sure the function was properly defined and imported before calling it."
            ]

        return [
            "Check the line where the error occurred for type mismatches.",
            "Verify the types of variables passed to functions or operators.",
            "Add explicit type conversion if necessary."
        ]
