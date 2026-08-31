"""Diagnostic rule for syntax and code compilation parse errors."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

SYNTAX_ERROR_REGEX = re.compile(
    r"(?:(?:SyntaxError:\s*(?P<py_syn>[^\n]+))|"
    r"(?:IndentationError:\s*(?P<py_indent>[^\n]+))|"
    r"(?:SyntaxError:\s*Unexpected token\s*(?P<js_token>[^\n]+))|"
    r"(?:Parse error:\s*syntax error,\s*(?P<php_syn>[^\n]+))|"
    r"(?:error:\s*expected\s*['\"]?(?P<c_syn>[^'\"]+)['\"]?\s*before))",
    re.IGNORECASE
)

class SyntaxErrorRule(BaseDiagnosticRule):
    """Diagnoses syntax errors, indentation errors, and invalid language tokens."""

    rule_id = "syntax-error"
    name = "Syntax Error"
    category = "code"
    priority = 65

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        match = SYNTAX_ERROR_REGEX.search(cleaned_output)
        if match:
            detail = (
                match.group("py_syn") or
                match.group("py_indent") or
                match.group("js_token") or
                match.group("php_syn") or
                match.group("c_syn") or
                "invalid syntax"
            )
            is_indent = "IndentationError" in cleaned_output
            title = "💀 IndentationError" if is_indent else "💀 SyntaxError"
            return RuleMatch(
                matched=True,
                title=f"{title}: {detail}",
                original_error=match.group(0).strip().splitlines()[0],
                extracted_vars={
                    "detail": detail,
                    "is_indent": is_indent
                }
            )
        
        if "SyntaxError" in cleaned_output:
            return RuleMatch(
                matched=True,
                title="💀 SyntaxError",
                original_error="SyntaxError: Invalid code syntax",
                extracted_vars={
                    "detail": "syntax error",
                    "is_indent": False
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        detail = vars.get("detail", "invalid syntax")
        is_indent = vars.get("is_indent", False)
        if is_indent:
            return (
                f"Your code contains inconsistent indentation ({detail}). "
                "Python requires strict indentation (usually 4 spaces) to define code blocks."
            )
        return (
            f"The interpreter/compiler encountered code it cannot parse ({detail}). "
            "This is usually caused by an unclosed bracket, missing comma/colon, or typo."
        )

    def generate_human_explanation(self, vars: Dict[str, Any]) -> str:
        is_indent = vars.get("is_indent", False)
        if is_indent:
            return (
                "Python is very picky about its spaces.\n"
                "A line is indented too far or not far enough."
            )
        return (
            "The computer cannot understand this sentence.\n"
            "Look for a missing quote, bracket, parenthesis, or colon near the indicated line."
        )

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        is_indent = vars.get("is_indent", False)
        if is_indent:
            return [
                "Inspect the line indicated in the 'Where' section.",
                "Ensure you are using 4 spaces consistently and not mixing tabs and spaces.",
                "Check the lines immediately before and after for alignment."
            ]
        return [
            "Check the exact line and column shown in 'Where' above.",
            "Check for unclosed quotes (`\"` or `'`), parentheses `()`, brackets `[]`, or braces `{}`.",
            "Check the preceding line — syntax errors often originate from an unclosed token on the line right before."
        ]
