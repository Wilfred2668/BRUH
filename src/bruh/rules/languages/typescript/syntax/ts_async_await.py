"""Diagnostic rule for TypeScript async/await syntax and top-level await errors (TS1308, TS1375)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_ASYNC_AWAIT_REGEX = re.compile(
    r"error\s+TS(?P<code>1308|1375):\s*(?:'await'\s+expressions\s+are\s+only\s+allowed\s+within\s+async\s+functions|"
    r"'await'\s+expressions\s+are\s+only\s+allowed\s+at\s+the\s+top\s+level)",
    re.IGNORECASE
)

class TSAsyncAwaitRule(BaseDiagnosticRule):
    """Diagnoses TypeScript await expressions used outside async functions or invalid top-level contexts (TS1308, TS1375)."""

    rule_id = "ts-async-await"
    name = "TypeScript Async/Await Usage"
    category = "syntax"
    priority = 84

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = TS_ASYNC_AWAIT_REGEX.search(cleaned_output)
        if match:
            code = match.group("code")
            raw_err = match.group(0).strip()

            title = f"💀 'await' used outside async function or module context (TS{code})"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "code": code,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        code = vars.get("code")
        if code == "1375":
            return (
                "Top-level 'await' expressions are only allowed in files treated as ES modules. "
                "This file is currently treated as a global script because it has no import or export statements."
            )
        return "The 'await' operator can only be used inside functions declared with the 'async' modifier or in top-level modules."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        code = vars.get("code")
        if code == "1375":
            return [
                "Add an export statement to treat this file as a module: `export {};` at the end of the file.",
                "Ensure your `tsconfig.json` sets `module: es2022`, `esnext`, `nodenext`, or `node16`.",
                "Wrap your asynchronous logic inside an `async function main() { ... } main();`."
            ]

        return [
            "Add the `async` keyword to the enclosing function declaration: `async function fn() { ... }` or `async () => { ... }`.",
            "Use standard Promise chaining `.then((result) => { ... })` if the function cannot be async.",
            "Wrap the await expression in an Immediately Invoked Async Function Expression: `(async () => { await ... })();`."
        ]
