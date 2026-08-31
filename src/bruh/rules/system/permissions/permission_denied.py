import sys
import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

PERMISSION_REGEX = re.compile(
    r"(?:(?:PermissionError:\s*\[Errno 13\]\s*Permission denied:\s*['\"]?(?P<path1>[^'\"]+)['\"]?)|"
    r"(?:EACCES:\s*permission denied,\s*(?:[a-z_]+)\s*['\"]?(?P<path2>[^'\"]+)['\"]?)|"
    r"(?:npm ERR!\s*path\s+(?P<path3>[^\r\n]+))|"
    r"(?:npm ERR!\s*code EACCES)|"
    r"(?:(?P<path4>[^\s:]+):\s*Permission denied)|"
    r"(?:Access is denied)|"
    r"(?:UnauthorizedAccessException))",
    re.IGNORECASE
)

class PermissionDeniedRule(BaseDiagnosticRule):
    """Diagnoses file system or execution permission issues."""

    rule_id = "permission-denied"
    name = "Permission Denied"
    category = "security"
    priority = 85

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        match = PERMISSION_REGEX.search(cleaned_output)
        if match:
            # Look for secondary path info if first matched generic EACCES
            path = match.group("path1") or match.group("path2") or match.group("path3") or match.group("path4") or ""
            if not path:
                path_match = re.search(r"(?:npm ERR!\s*path|permission denied,\s*(?:[a-z_]+))\s*['\"]?(?P<subpath>[^'\"\r\n]+)['\"]?", cleaned_output, re.IGNORECASE)
                if path_match:
                    path = path_match.group("subpath").strip()
            
            title = "💀 Permission Denied"
            if path:
                title += f": {path}"
            return RuleMatch(
                matched=True,
                title=title,
                original_error=match.group(0).strip().splitlines()[0],
                extracted_vars={
                    "path": path,
                    "code": "EACCES / Errno 13"
                }
            )

        if exit_code == 126 and command:
            return RuleMatch(
                matched=True,
                title="💀 Permission Denied (Cannot Execute)",
                original_error=f"Exit code 126: {command} cannot be executed",
                extracted_vars={
                    "path": command.split()[0],
                    "code": "126"
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        path = vars.get("path")
        if path:
            return (
                f"Your process tried to read, write, or execute '{path}', "
                "but your user account does not have sufficient permissions."
            )
        return (
            "The operation failed because the current user account does not have "
            "sufficient read, write, or execute permissions for this file or directory."
        )

    def generate_human_explanation(self, vars: Dict[str, Any]) -> str:
        return (
            "The operating system locked the door and didn't give your process the key.\n"
            "You need higher privileges or permission flags (like chmod or Run as Administrator)."
        )

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        path = vars.get("path", "")
        is_windows = sys.platform == "win32"
        suggestions = []

        if is_windows:
            if path:
                suggestions.append(f"Check if '{path}' is open or locked by another application.")
            suggestions.append("Try running your terminal as Administrator if editing protected folders.")
            suggestions.append("Check file and folder permissions in File Properties.")
        else:
            if path:
                suggestions.append(f"Check file permissions: `ls -la {path}`")
                suggestions.append(f"If it's a script, make it executable: `chmod +x {path}`")
            else:
                suggestions.append("Check ownership and permissions of your project files.")
            suggestions.append("Avoid running npm with `sudo`; fix directory permissions instead.")

        return suggestions[:3]
