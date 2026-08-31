"""Diagnostic rule for missing dependencies, packages, and uninstalled modules."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

PYTHON_MODULE_REGEX = re.compile(
    r"(?:(?:ModuleNotFoundError|ImportError):\s*No module named ['\"](?P<mod1>[^'\"]+)['\"])",
    re.IGNORECASE
)

NODE_MODULE_REGEX = re.compile(
    r"(?:(?:Error:\s*Cannot find module ['\"](?P<node_mod>[^'\"]+)['\"])|"
    r"MODULE_NOT_FOUND)",
    re.IGNORECASE
)

GO_PACKAGE_REGEX = re.compile(
    r'cannot find package "(?P<go_pkg>[^"]+)" in any of:',
    re.IGNORECASE
)

RUST_CRATE_REGEX = re.compile(
    r"(?:can't find crate for `(?P<crate>[^`]+)`|unresolved import `(?P<crate2>[^`]+)`)",
    re.IGNORECASE
)

class ModuleNotFoundRule(BaseDiagnosticRule):
    """Diagnoses missing or uninstalled libraries in Python, Node.js, Go, and Rust."""

    rule_id = "module-not-found"
    name = "Module not found"
    category = "dependency"
    priority = 90

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        # 1. Python Module Not Found
        py_match = PYTHON_MODULE_REGEX.search(cleaned_output)
        if py_match:
            module = py_match.group("mod1") or py_match.group("mod2") or "module"
            top_level = module.split(".")[0]
            return RuleMatch(
                matched=True,
                title="💀 Module not found",
                original_error=f"No module named '{module}'",
                extracted_vars={
                    "module": module,
                    "top_module": top_level,
                    "ecosystem": "python"
                }
            )

        # 2. Go Package Not Found
        go_match = GO_PACKAGE_REGEX.search(cleaned_output)
        if go_match:
            pkg = go_match.group("go_pkg")
            return RuleMatch(
                matched=True,
                title="💀 Module not found",
                original_error=f'cannot find package "{pkg}"',
                extracted_vars={
                    "module": pkg,
                    "ecosystem": "go"
                }
            )

        # 4. Rust Crate Not Found
        rust_match = RUST_CRATE_REGEX.search(cleaned_output)
        if rust_match:
            crate = rust_match.group("crate") or rust_match.group("crate2") or "crate"
            return RuleMatch(
                matched=True,
                title="💀 Module not found",
                original_error=f"can't find crate for `{crate}`",
                extracted_vars={
                    "module": crate,
                    "ecosystem": "rust"
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        module = vars.get("module", "the module")
        ecosystem = vars.get("ecosystem", "")

        if ecosystem == "python":
            return f"Python tried to import '{module}', but it isn't available in the active Python environment."
        elif ecosystem == "node":
            return f"Node tried to load '{module}', but it isn't available in this project."
        elif ecosystem == "go":
            return f"Go cannot locate package '{module}' in your GOPATH or Go modules cache."
        elif ecosystem == "rust":
            return f"Rust compiler cannot find crate or module `{module}`."

        return f"The program tried to import '{module}', but the package is not installed."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        module = vars.get("top_module") or vars.get("module", "package")
        ecosystem = vars.get("ecosystem", "")

        if ecosystem == "python":
            return [
                f"Check the import statement for typos: '{module}'.",
                "Make sure your virtual environment (venv/conda) is activated.",
                f"If not installed, install it: `pip install {module}`"
            ]
        elif ecosystem == "node":
            return [
                "Check the module name for a typo.",
                "Check whether it is listed in package.json.",
                "If it should be a dependency, run `npm install`."
            ]
        elif ecosystem == "go":
            return [
                f"Check package name spelling: '{module}'.",
                f"Download the missing package: `go get {module}`"
            ]
        elif ecosystem == "rust":
            return [
                f"Add the crate to Cargo.toml: `cargo add {module}`",
                "Run `cargo build` to fetch dependencies."
            ]
        return [
            f"Check that '{module}' is spelled correctly.",
            "Make sure your development environment is activated.",
            f"Install {module} if necessary."
        ]
