"""Diagnostic rule for TypeScript missing module and type declaration errors (TS2307, TS2792)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

TS_MODULE_NOT_FOUND_REGEX = re.compile(
    r"error\s+TS(?:2307|2792):\s*Cannot find module\s+'(?P<module>[^']+)'(?:\s+or its corresponding type declarations)?",
    re.IGNORECASE
)

class TSModuleNotFoundRule(BaseDiagnosticRule):
    """Diagnoses TypeScript cannot find module or type declarations errors (TS2307, TS2792)."""

    rule_id = "ts-module-not-found"
    name = "TypeScript Module Not Found"
    category = "modules"
    priority = 92

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = TS_MODULE_NOT_FOUND_REGEX.search(cleaned_output)
        if match:
            module = match.group("module")
            raw_err = match.group(0).strip()

            is_local = module.startswith(".") or module.startswith("/") or module.startswith("\\")

            if is_local:
                title = f"💀 Cannot find local module '{module}' (TS2307)"
            else:
                title = f"💀 Cannot find module or type declarations for '{module}' (TS2307)"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "module": module,
                    "is_local": is_local,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        module = vars.get("module", "module")
        is_local = vars.get("is_local", False)

        if is_local:
            return f"TypeScript cannot find a local file or type definition (`.ts`, `.tsx`, `.d.ts`) at relative path '{module}'."

        return (
            f"TypeScript cannot find the npm package '{module}' or its TypeScript type definitions "
            f"in your project's node_modules directory."
        )

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        module = vars.get("module", "module")
        is_local = vars.get("is_local", False)

        if is_local:
            return [
                f"Verify the relative file path '{module}' exists relative to the importing file.",
                "Ensure the target file has a valid TypeScript/JavaScript extension (`.ts`, `.tsx`, `.d.ts`, `.js`).",
                "If using path aliases (e.g. `@/components`), verify `paths` and `baseUrl` in `tsconfig.json`."
            ]

        return [
            f"Install the npm package: `npm install {module}` (or `pnpm add {module}` / `yarn add {module}`).",
            f"Install the community type definitions if not bundled: `npm install -D @types/{module}`.",
            "If the module lacks types, create a declaration file `declarations.d.ts` containing `declare module '{module}';`."
        ]
