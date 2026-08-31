"""Diagnostic rule for missing directories and path navigation errors."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

DIRECTORY_NOT_FOUND_REGEX = re.compile(
    r"(?:(?:Cannot find path ['\"]?(?P<dir1>[^\r\n'\"]+)['\"]? because it does not exist)|"
    r"(?:cd:\s*no such file or directory:\s*(?P<dir2>[^\r\n]+))|"
    r"(?:Set-Location\s*:.*?Cannot find path ['\"]?(?P<dir3>[^\r\n'\"]+)['\"]?)|"
    r"(?:The system cannot find the path specified))",
    re.IGNORECASE
)

class DirectoryNotFoundRule(BaseDiagnosticRule):
    """Diagnoses missing directories when changing directories or specifying folder paths."""

    rule_id = "directory-not-found"
    name = "Directory not found"
    category = "filesystem"
    priority = 88

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        match = DIRECTORY_NOT_FOUND_REGEX.search(cleaned_output)
        if match:
            folder = match.group("dir1") or match.group("dir2") or match.group("dir3") or ""
            return RuleMatch(
                matched=True,
                title="💀 Directory not found",
                original_error=match.group(0).strip(),
                extracted_vars={"folder": folder}
            )

        cmd_lower = (command or "").strip().lower()
        if (cmd_lower.startswith("cd ") or cmd_lower.startswith("set-location ")) and (
            "does not exist" in cleaned_output.lower() or "no such file or directory" in cleaned_output.lower() or "cannot find path" in cleaned_output.lower()
        ):
            folder = command.strip().split(maxsplit=1)[1].strip(" '\"") if " " in command else ""
            return RuleMatch(
                matched=True,
                title="💀 Directory not found",
                original_error=cleaned_output.splitlines()[0] if cleaned_output else "Cannot find path",
                extracted_vars={"folder": folder}
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        return "You tried to enter a directory that doesn't exist at that location."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        return [
            "Check the folder name for a typo.",
            "Check which folder you're currently in.",
            "If the folder should exist, create it or go to the correct location."
        ]
