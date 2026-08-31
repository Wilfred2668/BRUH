"""Diagnostic rule for JavaScript / Node.js JSON.parse errors."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

# 1. Modern Node.js / V8 format: SyntaxError: "[object Object]" is not valid JSON
# or SyntaxError: Unexpected token '}', "{"name":}" is not valid JSON
JS_JSON_NOT_VALID_REGEX = re.compile(
    r"SyntaxError:\s*(?:Unexpected token\s*(?P<token>'[^']+'|[^\s,]+),\s*)?(?P<sample>\"[^\r\n]*\"|'[^'\r\n]*'|[^\r\n]+)\s+is not valid JSON",
    re.IGNORECASE
)

# 2. Position-based V8 / Node format: SyntaxError: Unexpected token } in JSON at position 15
# or SyntaxError: Expected property name or '}' in JSON at position 10
JS_JSON_POSITION_REGEX = re.compile(
    r"SyntaxError:\s*(?:(?:Unexpected token\s*(?P<token>'[^']+'|[^\s,]+)\s+in JSON at position\s*(?P<pos>\d+))|(?:(?P<expected>Expected\s+[^\r\n]+)\s+in JSON at position\s*(?P<pos2>\d+)))",
    re.IGNORECASE
)

# 3. Unexpected end of JSON input
JS_JSON_END_OF_INPUT_REGEX = re.compile(
    r"SyntaxError:\s*Unexpected end of JSON input",
    re.IGNORECASE
)

# 4. Engine-prefixed format: SyntaxError: JSON.parse: unexpected character ...
JS_JSON_PARSE_PREFIX_REGEX = re.compile(
    r"SyntaxError:\s*JSON\.?parse(?:\s+error)?:\s*(?P<msg>[^\r\n]+)",
    re.IGNORECASE
)

# 5. Generic SyntaxError regex used when stack trace contains `at JSON.parse`
JS_GENERIC_SYNTAX_WITH_JSON_PARSE = re.compile(
    r"SyntaxError:\s*(?P<msg>[^\r\n]+)",
    re.IGNORECASE
)

class JSJSONParseErrorRule(BaseDiagnosticRule):
    """Diagnoses malformed JSON syntax in JavaScript JSON.parse() calls."""

    rule_id = "js-json-parse-error"
    name = "JavaScript JSON Parse Error"
    category = "runtime"
    priority = 79

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        # 1. Match "... is not valid JSON" (Modern Node 18+)
        m_not_valid = JS_JSON_NOT_VALID_REGEX.search(cleaned_output)
        if m_not_valid:
            token = m_not_valid.group("token")
            sample = m_not_valid.group("sample")
            raw_err = m_not_valid.group(0).strip()
            is_object = bool(sample and "[object Object]" in sample)

            if is_object:
                title = "💀 JSON Parse Error: '[object Object]' is not valid JSON"
            elif token:
                title = f"💀 JSON Parse Error: Unexpected token {token}"
            else:
                title = "💀 JSON Parse Error: Input is not valid JSON"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "token": token,
                    "sample": sample,
                    "is_object_coercion": is_object,
                    "raw": raw_err
                }
            )

        # 2. Match "... in JSON at position X"
        m_pos = JS_JSON_POSITION_REGEX.search(cleaned_output)
        if m_pos:
            token = m_pos.group("token")
            expected = m_pos.group("expected")
            pos = m_pos.group("pos") or m_pos.group("pos2")
            raw_err = m_pos.group(0).strip()

            if token and pos:
                title = f"💀 JSON Parse Error: Unexpected token {token} at position {pos}"
            elif expected and pos:
                title = f"💀 JSON Parse Error: {expected.strip()} (position {pos})"
            elif pos:
                title = f"💀 JSON Parse Error at position {pos}"
            else:
                title = "💀 JSON Parse Error (SyntaxError)"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "token": token,
                    "pos": pos,
                    "expected": expected,
                    "raw": raw_err
                }
            )

        # 3. Match "Unexpected end of JSON input"
        m_end = JS_JSON_END_OF_INPUT_REGEX.search(cleaned_output)
        if m_end:
            raw_err = m_end.group(0).strip()
            return RuleMatch(
                matched=True,
                title="💀 JSON Parse Error: Unexpected end of JSON input",
                original_error=raw_err,
                extracted_vars={"msg": "Unexpected end of JSON input", "raw": raw_err}
            )

        # 4. Match "JSON.parse: ..." or "JSON Parse error: ..."
        m_prefix = JS_JSON_PARSE_PREFIX_REGEX.search(cleaned_output)
        if m_prefix:
            raw_err = m_prefix.group(0).strip()
            msg = m_prefix.group("msg")
            return RuleMatch(
                matched=True,
                title=f"💀 JSON Parse Error: {msg.strip()}",
                original_error=raw_err,
                extracted_vars={"msg": msg, "raw": raw_err}
            )

        # 5. Fallback: If stack trace explicitly indicates JSON.parse caused the SyntaxError
        if "at JSON.parse" in cleaned_output:
            m_gen = JS_GENERIC_SYNTAX_WITH_JSON_PARSE.search(cleaned_output)
            if m_gen:
                raw_err = m_gen.group(0).strip()
                msg = m_gen.group("msg").strip()
                return RuleMatch(
                    matched=True,
                    title=f"💀 JSON Parse Error: {msg}",
                    original_error=raw_err,
                    extracted_vars={"msg": msg, "raw": raw_err}
                )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        if vars.get("is_object_coercion"):
            return "JSON.parse() was passed a JavaScript object or non-string value instead of a JSON string. JavaScript coerced it to '[object Object]', which is not valid JSON."

        pos = vars.get("pos")
        token = vars.get("token")
        sample = vars.get("sample")

        if pos and token:
            return f"JSON.parse() encountered an invalid token {token} at character position {pos} while parsing a JSON string."
        elif pos:
            return f"JSON.parse() failed because the input string has invalid JSON syntax at character position {pos}."
        elif token:
            return f"JSON.parse() failed due to an unexpected token {token} in the JSON input."
        elif sample:
            return f"JSON.parse() failed because the input {sample} is not formatted as valid JSON."

        return "JSON.parse() failed because the input string is not formatted as valid JSON."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        if vars.get("is_object_coercion"):
            return [
                "Do not call JSON.parse() on an object that is already parsed or deserialized.",
                "If you intended to convert a JavaScript object into a JSON string, use `JSON.stringify(obj)` instead.",
                "Verify the type of the value passed to JSON.parse() using `typeof data === 'string'`."
            ]

        pos = vars.get("pos")
        pos_hint = f"around character position {pos}" if pos else "in the JSON string"

        return [
            f"Check the JSON payload {pos_hint} for syntax errors (e.g. trailing commas, single quotes, or missing double quotes).",
            "Ensure all object keys and string values are enclosed in double quotes (`\"key\": \"value\"`), as JSON does not permit single quotes.",
            "If reading from a web server or fetch() response, ensure the endpoint returned valid JSON instead of an HTML error page (e.g. 502/404)."
        ]
