"""Diagnostic rule for packages not found in package registries (PyPI, npm)."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

PIP_PKG_NOT_FOUND_REGEX = re.compile(
    r"(?:(?:ERROR:\s*Could not find a version that satisfies the requirement\s*(?P<pkg1>[a-zA-Z0-9_\-\.]+)|"
    r"ERROR:\s*No matching distribution found for\s*(?P<pkg2>[a-zA-Z0-9_\-\.]+)))",
    re.IGNORECASE
)

NPM_PKG_NOT_FOUND_REGEX = re.compile(
    r"(?:(?:npm error 404 Not Found.*?registry\.npmjs\.org/(?P<npm_pkg>[^\s/]+)|"
    r"npm ERR!\s*404\s*Not Found\s*-\s*GET\s*https://registry\.npmjs\.org/(?P<npm_pkg2>[^\s/]+)))",
    re.IGNORECASE
)

class PackageNotFoundRule(BaseDiagnosticRule):
    """Diagnoses packages missing from online package registries like PyPI or npm."""

    rule_id = "package-not-found"
    name = "Package not found"
    category = "dependency"
    priority = 92

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        pip_match = PIP_PKG_NOT_FOUND_REGEX.search(cleaned_output)
        if pip_match:
            pkg = pip_match.group("pkg1") or pip_match.group("pkg2") or "package"
            return RuleMatch(
                matched=True,
                title="💀 Package not found",
                original_error=pkg,
                extracted_vars={"package": pkg, "ecosystem": "pip"}
            )

        npm_match = NPM_PKG_NOT_FOUND_REGEX.search(cleaned_output)
        if npm_match:
            pkg = npm_match.group("npm_pkg") or npm_match.group("npm_pkg2") or "package"
            return RuleMatch(
                matched=True,
                title="💀 Package not found",
                original_error=pkg,
                extracted_vars={"package": pkg, "ecosystem": "npm"}
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        pkg = vars.get("package", "the package")
        ecosystem = vars.get("ecosystem", "The package manager")
        return f"{ecosystem} couldn't find a package called {pkg} that it can install."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        return [
            "Check the package name for a typo.",
            "Make sure you're using the package's real name.",
            "If you're following a tutorial, check that the package hasn't been renamed or removed."
        ]
