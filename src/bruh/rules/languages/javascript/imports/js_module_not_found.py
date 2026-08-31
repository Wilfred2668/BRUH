"""Diagnostic rule for Node.js Cannot find module / MODULE_NOT_FOUND errors."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

JS_MODULE_ERR_REGEX = re.compile(
    r"(?:(?:Error:\s*Cannot find module\s*'(?P<mod>[^']+)')|"
    r"(?:Cannot find module\s*\"(?P<mod2>[^\"]+)\")|"
    r"(?:code:\s*'MODULE_NOT_FOUND')|"
    r"(?:ERR_MODULE_NOT_FOUND))",
    re.IGNORECASE
)

class JSModuleNotFoundRule(BaseDiagnosticRule):
    """Diagnoses missing npm packages and unresolved local module imports in Node.js."""

    rule_id = "js-module-not-found"
    name = "Node.js Module Not Found"
    category = "dependency"
    priority = 90

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = JS_MODULE_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            mod_name = match.group("mod") or match.group("mod2")

            # Fallback search if regex hit code: 'MODULE_NOT_FOUND'
            if not mod_name:
                mod_match = re.search(r"Cannot find module\s*['\"]([^'\"]+)['\"]", cleaned_output)
                if mod_match:
                    mod_name = mod_match.group(1)

            is_local = False
            if mod_name and (mod_name.startswith(".") or mod_name.startswith("/")):
                is_local = True

            if is_local and mod_name:
                title = f"💀 Cannot find local module '{mod_name}'"
            elif mod_name:
                title = f"💀 Cannot find package '{mod_name}' (MODULE_NOT_FOUND)"
            else:
                title = "💀 Node.js Module Not Found (MODULE_NOT_FOUND)"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "module": mod_name,
                    "is_local": is_local,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        mod_name = vars.get("module")
        is_local = vars.get("is_local")

        if is_local and mod_name:
            return (
                f"Node.js attempted to load a local file from path '{mod_name}', "
                f"but no file exists at that relative path."
            )
        elif mod_name:
            return (
                f"Node.js attempted to require or import '{mod_name}', but it is not installed "
                f"in your project's 'node_modules' directory or package dependencies."
            )

        return "Node.js cannot resolve the requested module or dependency."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        mod_name = vars.get("module")
        is_local = vars.get("is_local")

        if is_local and mod_name:
            return [
                f"Check the module name for a typo: '{mod_name}'.",
                f"Check that the file exists at the relative path '{mod_name}' from the importing file.",
                "Verify file extension (`.js`, `.mjs`, `.cjs`, `.json`) or ensure your bundler supports extensionless imports.",
                "Check for casing typos in the filename on case-sensitive filesystems (Linux/macOS)."
            ]
        elif mod_name:
            return [
                f"Check the module name for a typo: '{mod_name}'.",
                f"Install the missing npm package: `npm install {mod_name}` (or `pnpm add {mod_name}` / `yarn add {mod_name}`).",
                f"If '{mod_name}' is already in package.json, run `npm install` to populate node_modules."
            ]

        return [
            "Check the module name for a typo.",
            "Run `npm install` to ensure all project dependencies are installed.",
            "Verify the module path in your `import` or `require` statements."
        ]
