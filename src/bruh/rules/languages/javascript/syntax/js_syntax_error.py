"""Diagnostic rule for JavaScript / Node.js SyntaxError."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

JS_SYNTAX_ERR_REGEX = re.compile(
    r"(?:SyntaxError:\s*(?P<msg>Unexpected token\s*(?:'[^']+'|[^\s,]+)|Unexpected identifier(?:\s+'[^']+'|[^\r\n,]+)?|missing\s+[^\r\n]+|Unexpected end of input|Identifier\s+'[^']+'\s+has already been declared|Invalid or unexpected token|Cannot use import statement outside a module))",
    re.IGNORECASE
)

class JSSyntaxErrorRule(BaseDiagnosticRule):
    """Diagnoses syntax and parsing errors in JavaScript / Node.js code."""

    rule_id = "js-syntax-error"
    name = "JavaScript SyntaxError"
    category = "code"
    priority = 78

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        # Exclude JSON parse errors which are handled with higher specificity by JSON parse rules
        if "in json at position" in cleaned_output.lower() or "is not valid json" in cleaned_output.lower() or "json.parse" in cleaned_output.lower():
            return None

        match = JS_SYNTAX_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            msg = match.group("msg") or ""

            if msg:
                title = f"💀 SyntaxError: {msg.strip()}"
            else:
                title = "💀 JavaScript SyntaxError"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={"msg": msg, "raw": raw_err}
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        msg = vars.get("msg", "")
        if "already been declared" in msg:
            return f"A variable identifier was declared multiple times in the same block scope using 'let' or 'const'."
        elif "unexpected token" in msg.lower():
            return f"The JavaScript parser encountered an unexpected character or symbol ({msg}) that violates language grammar."
        elif "unexpected end of input" in msg.lower():
            return "The JavaScript file ended unexpectedly before all open brackets, braces, parentheses, or string quotes were closed."

        return "JavaScript encountered code that violates the language grammar and cannot be parsed."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        msg = vars.get("msg", "")
        if "already been declared" in msg:
            return [
                "Remove duplicate variable declarations or rename one of the variables.",
                "If reassigning an existing variable, do not re-declare it with `let` or `const`."
            ]

        return [
            "Check the exact line and column indicated in the stack trace.",
            "Look for unclosed or mismatched parentheses `()`, curly braces `{}`, or square brackets `[]`.",
            "Check for missing commas between array elements or object properties.",
            "If using modern syntax (e.g. JSX, TypeScript, decorators), verify your build/transpile toolchain (Babel/tsc/esbuild) is configured."
        ]
