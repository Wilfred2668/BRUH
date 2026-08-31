"""Diagnostic rule for missing files and file path errors."""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

FILE_NOT_FOUND_REGEX = re.compile(
    r"(?:(?:FileNotFoundError:\s*\[Errno 2\]\s*No such file or directory:\s*['\"](?P<path1>[^'\"]+)['\"])|"
    r"(?:ENOENT:\s*no such file or directory,\s*(?:open|stat|scandir|mkdir|read)\s*['\"](?P<path2>[^'\"]+)['\"])|"
    r"(?:can't open file ['\"](?P<path3>[^'\"]+)['\"]:?\s*\[Errno 2\])|"
    r"(?:npm error enoent.*?open ['\"](?P<path4>[^'\"]+)['\"])|"
    r"(?:npm error enoent Could not read (?P<path5>[^:]+):)|"
    r"(?:npm error path (?P<path6>[^\r\n]+))|"
    r"(?:No such file or directory:\s*['\"]?(?P<path7>[^\r\n'\"]+)['\"]?)|"
    r"(?:The system cannot find the file specified))",
    re.IGNORECASE
)

class FileNotFoundRule(BaseDiagnosticRule):
    """Diagnoses missing files when running programs or reading files."""

    rule_id = "file-not-found"
    name = "File not found"
    category = "filesystem"
    priority = 85

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        match = FILE_NOT_FOUND_REGEX.search(cleaned_output)
        if match:
            path = (
                match.group("path1") or
                match.group("path2") or
                match.group("path3") or
                match.group("path4") or
                match.group("path5") or
                match.group("path6") or
                match.group("path7") or
                ""
            )
            is_pkg_json = "package.json" in path.lower() or "package.json" in cleaned_output.lower()

            if is_pkg_json:
                return RuleMatch(
                    matched=True,
                    title="💀 npm: package.json not found",
                    original_error="npm error path package.json",
                    extracted_vars={"path": "package.json", "is_package_json": True}
                )

            norm_path = path.replace("\\", "/").rstrip("/") if path else ""
            filename = norm_path.split("/")[-1] if norm_path else (command.split()[-1] if command else "file")
            return RuleMatch(
                matched=True,
                title="💀 File not found",
                original_error=path if path else filename,
                extracted_vars={"path": path if path else filename, "filename": filename, "is_package_json": False, "command": command or ""}
            )

        return None

    def _get_filename(self, vars: Dict[str, Any]) -> str:
        if vars.get("filename"):
            return vars["filename"]
        path = vars.get("path", "")
        if path:
            norm = path.replace("\\", "/").rstrip("/")
            return norm.split("/")[-1] if norm else "the file"
        return "the file"

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        filename = self._get_filename(vars)
        if vars.get("is_package_json"):
            return "npm could not find a package.json file in this directory."
        
        cmd = (vars.get("command") or "").lower()
        if "python" in cmd:
            return f"Python tried to open {filename}, but that file isn't in the current folder."
        elif "node" in cmd:
            return f"Node tried to open {filename}, but that file isn't in the current folder."
        return f"The program tried to open {filename}, but it doesn't exist in the current directory."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        filename = self._get_filename(vars)
        if vars.get("is_package_json"):
            return [
                "Make sure you are in the root directory of your Node project (check with pwd / cd).",
                "If this is a new project, create package.json: `npm init -y`",
                "If package.json already exists in a subfolder, navigate there before running your command."
            ]

        return [
            f"Check that {filename} exists.",
            f"Check the filename for a typo.",
            "Make sure you're in the correct project folder."
        ]
