"""Diagnostic rule for ValueError conversions, unpacking, and search failures."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

VALUE_ERR_REGEX = re.compile(
    r"(?:(?:ValueError:\s*invalid literal for int\(\) with base \d+:\s*['\"](?P<int_lit>[^'\"]+)['\"])|"
    r"(?:ValueError:\s*could not convert string to float:\s*['\"](?P<flt_lit>[^'\"]+)['\"])|"
    r"(?:ValueError:\s*not enough values to unpack \(expected (?P<exp_u>\d+),\s*got (?P<got_u>\d+)\))|"
    r"(?:ValueError:\s*too many values to unpack \(expected (?P<exp_u2>\d+)\))|"
    r"(?:ValueError:\s*['\"](?P<not_in_list>[^'\"]+)['\"]\s*is not in list))",
    re.IGNORECASE
)

class ValueErrorRule(BaseDiagnosticRule):
    """Diagnoses value conversion failures, tuple unpacking mismatches, and sequence search errors."""

    rule_id = "value-error"
    name = "ValueError"
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

        match = VALUE_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            int_lit = match.group("int_lit")
            flt_lit = match.group("flt_lit")
            exp_u = match.group("exp_u")
            got_u = match.group("got_u")
            exp_u2 = match.group("exp_u2")
            not_in_list = match.group("not_in_list")

            if int_lit:
                title = f"💀 ValueError: invalid int literal '{int_lit}'"
                kind = "int_conv"
            elif flt_lit:
                title = f"💀 ValueError: cannot convert '{flt_lit}' to float"
                kind = "float_conv"
            elif exp_u and got_u:
                title = f"💀 ValueError: not enough values to unpack (expected {exp_u}, got {got_u})"
                kind = "unpack_few"
            elif exp_u2:
                title = f"💀 ValueError: too many values to unpack (expected {exp_u2})"
                kind = "unpack_many"
            elif not_in_list:
                title = f"💀 ValueError: '{not_in_list}' is not in list"
                kind = "not_in_list"
            else:
                title = "💀 ValueError: Invalid Value"
                kind = "generic"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "kind": kind,
                    "int_lit": int_lit,
                    "flt_lit": flt_lit,
                    "exp_u": exp_u or exp_u2,
                    "got_u": got_u,
                    "not_in_list": not_in_list,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        kind = vars.get("kind", "generic")

        if kind == "int_conv":
            return f"Python attempted to parse the string '{vars.get('int_lit')}' into an integer, but it contains non-numeric characters or decimals."
        elif kind == "float_conv":
            return f"Python attempted to parse '{vars.get('flt_lit')}' into a float, but it could not be converted to a valid number."
        elif kind == "unpack_few":
            return f"You tried to unpack a sequence into {vars.get('exp_u')} variables, but the sequence only contained {vars.get('got_u')} item(s)."
        elif kind == "unpack_many":
            return f"You tried to unpack a sequence into {vars.get('exp_u')} variables, but the sequence contained more items than expected."
        elif kind == "not_in_list":
            return f"You called `.index()` or `.remove()` for '{vars.get('not_in_list')}', but that value is not present in the list."

        return "A function received an argument that has the right type but an inappropriate or unparseable value."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        kind = vars.get("kind", "generic")

        if kind in ("int_conv", "float_conv"):
            return [
                "Validate or clean the input string (e.g. `strip()` or remove formatting characters) before converting.",
                "If the string might contain decimal points, convert to float first (`int(float(value))`).",
                "Wrap the conversion in a `try/except ValueError` block if the input originates from user input."
            ]
        elif kind in ("unpack_few", "unpack_many"):
            return [
                "Check the length of the list or tuple before unpacking (`len(sequence)`).",
                "Use list indexing or star unpacking (e.g. `first, *rest = sequence`) to handle variable-length sequences.",
                "Ensure function return values match the number of receiving variables."
            ]
        elif kind == "not_in_list":
            return [
                f"Check whether '{vars.get('not_in_list')}' is in the list using `if '{vars.get('not_in_list')}' in my_list:` before searching or removing.",
                "Check for spelling or whitespace differences in the list items.",
                "Inspect the list contents with `print(my_list)` before calling `.index()`."
            ]

        return [
            "Check the argument value passed to the failing function.",
            "Add input validation to catch invalid values before processing.",
            "Inspect the value printed right before the error line."
        ]
