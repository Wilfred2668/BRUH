"""Diagnostic rule for package manager dependency tree and version conflicts."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

NPM_ERESOLVE_REGEX = re.compile(
    r"(?:npm ERR!\s*code ERESOLVE|npm ERR!\s*unable to resolve dependency tree|Conflicting peer dependency:\s*(?P<pkg>[^\s\n]+))",
    re.IGNORECASE
)

PIP_DIRECT_CONFLICT_REGEX = re.compile(
    r"(?:Cannot install (?P<p1>[a-zA-Z0-9_\-]+)==(?P<v1>[^\s]+) and (?P<p2>[a-zA-Z0-9_\-]+)==(?P<v2>[^\s]+)|"
    r"The user requested (?P<p3>[a-zA-Z0-9_\-]+)==(?P<v3>[^\s\n]+).*?The user requested (?P<p4>[a-zA-Z0-9_\-]+)==(?P<v4>[^\s\n]+))",
    re.DOTALL | re.IGNORECASE
)

PIP_GENERIC_CONFLICT_REGEX = re.compile(
    r"(?:ResolutionImpossible|Cannot install .*? because these package versions have conflicting dependencies|The conflict is caused by:\s*(?P<pip_pkg>[^\n]+))",
    re.IGNORECASE
)

CARGO_CONFLICT_REGEX = re.compile(
    r"(?:failed to select a version for the requirement `(?P<cargo_pkg>[^`]+)`|version conflict)",
    re.IGNORECASE
)

class DependencyConflictRule(BaseDiagnosticRule):
    """Diagnoses peer dependency conflicts and incompatible package version constraints."""

    rule_id = "dependency-conflict"
    name = "Dependency and Version Conflict"
    category = "dependency"
    priority = 70

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        # 1. pip direct same-package duplicate conflict
        pip_direct = PIP_DIRECT_CONFLICT_REGEX.search(cleaned_output)
        if pip_direct:
            pkg = pip_direct.group("p1") or pip_direct.group("p3") or "package"
            v1 = pip_direct.group("v1") or pip_direct.group("v3") or ""
            v2 = pip_direct.group("v2") or pip_direct.group("v4") or ""
            return RuleMatch(
                matched=True,
                title="💀 Dependency Conflict",
                original_error=f"Cannot install both {pkg}=={v1} and {pkg}=={v2}",
                extracted_vars={
                    "package": pkg,
                    "v1": v1,
                    "v2": v2,
                    "is_direct_duplicate": True,
                    "ecosystem": "pip"
                }
            )

        # 2. npm peer dependency conflict
        npm_match = NPM_ERESOLVE_REGEX.search(cleaned_output)
        if npm_match:
            pkg = npm_match.group("pkg") or "peer dependencies"
            return RuleMatch(
                matched=True,
                title="💀 npm: Dependency Resolution Conflict",
                original_error="npm ERR! ERESOLVE unable to resolve dependency tree",
                extracted_vars={
                    "package": pkg,
                    "is_direct_duplicate": False,
                    "ecosystem": "npm"
                }
            )

        # 3. pip general conflict
        pip_match = PIP_GENERIC_CONFLICT_REGEX.search(cleaned_output)
        if pip_match:
            pkg = pip_match.group("pip_pkg") or "packages"
            return RuleMatch(
                matched=True,
                title="💀 pip: Dependency Conflict",
                original_error="pip encountered conflicting version requirements",
                extracted_vars={
                    "package": pkg,
                    "is_direct_duplicate": False,
                    "ecosystem": "pip"
                }
            )

        # 4. Cargo conflict
        cargo_match = CARGO_CONFLICT_REGEX.search(cleaned_output)
        if cargo_match:
            pkg = cargo_match.group("cargo_pkg") or "crates"
            return RuleMatch(
                matched=True,
                title="💀 Cargo: Version Conflict",
                original_error=cargo_match.group(0),
                extracted_vars={
                    "package": pkg,
                    "is_direct_duplicate": False,
                    "ecosystem": "cargo"
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        ecosystem = vars.get("ecosystem", "package manager")
        if vars.get("is_direct_duplicate"):
            pkg = vars.get("package", "the package")
            v1 = vars.get("v1", "")
            v2 = vars.get("v2", "")
            return (
                f"You asked pip to install two different versions of `{pkg}`:\n\n"
                f"    {pkg} {v1}\n"
                f"    {pkg} {v2}\n\n"
                "pip can't install both versions at the same time."
            )
        if ecosystem == "npm":
            return (
                "npm could not install dependencies because two packages in your project "
                "require incompatible versions of the same peer dependency."
            )
        elif ecosystem == "pip":
            return (
                "pip could not find a set of package versions that satisfies all constraints "
                "in your requirements."
            )
        return "Two or more packages in your dependency tree require conflicting, incompatible versions."

    def generate_human_explanation(self, vars: Dict[str, Any]) -> str:
        if vars.get("is_direct_duplicate"):
            return "You asked for two different versions of the exact same library in one command."
        return "Two packages want different, incompatible versions of the same library."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        if vars.get("is_direct_duplicate"):
            return [
                "Pick the version you actually want and remove the other one.",
                "Check your command or requirements.txt for duplicate entries."
            ]
        ecosystem = vars.get("ecosystem", "npm")
        if ecosystem == "npm":
            return [
                "Try installing with legacy peer resolution: `npm install --legacy-peer-deps`",
                "Or update the older packages in package.json to compatible versions."
            ]
        elif ecosystem == "pip":
            return [
                "Review the conflicting packages in your requirements.txt.",
                "Try relaxing pinned versions (e.g. use `>=` instead of `==`)."
            ]
        return [
            "Check the version requirements of the conflicting packages.",
            "Upgrade older dependencies to align version constraints."
        ]
