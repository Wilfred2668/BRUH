"""Diagnostic rule for command not found errors across all shells."""

import re
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

COMMAND_NOT_FOUND_REGEX = re.compile(
    r"(?:(?:'|\")(?P<cmd1>[^'\"]+)(?:'|\")\s*is not recognized as an internal or external command|"
    r"The term ['\"](?P<cmd2>[^'\"]+)['\"]\s*is not recognized as the name of a cmdlet|"
    r"(?:bash:\s*)?(?P<cmd3>[^\s:]+):\s*command not found|"
    r"zsh:\s*command not found:\s*(?P<cmd4>[^\s\n]+)|"
    r"command not found:\s*(?P<cmd5>[^\s\n]+))",
    re.IGNORECASE
)

class CommandNotFoundRule(BaseDiagnosticRule):
    """Diagnoses missing or uninstalled CLI commands and typos in shell."""

    rule_id = "command-not-found"
    name = "Command Not Found"
    category = "shell"
    priority = 90

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        match = COMMAND_NOT_FOUND_REGEX.search(cleaned_output)
        if match:
            cmd = (
                match.group("cmd1") or
                match.group("cmd2") or
                match.group("cmd3") or
                match.group("cmd4") or
                match.group("cmd5")
            )
            return RuleMatch(
                matched=True,
                title=f"💀 Command not found: '{cmd}'",
                original_error=match.group(0).strip().splitlines()[0],
                extracted_vars={
                    "command": cmd,
                    "invoked_command": command or cmd
                }
            )

        if exit_code == 127 and command:
            cmd = command.split()[0] if command else "command"
            return RuleMatch(
                matched=True,
                title=f"💀 Command not found: '{cmd}'",
                original_error=f"Exit code 127: {cmd} not found in PATH",
                extracted_vars={
                    "command": cmd,
                    "invoked_command": command
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        cmd = vars.get("command", "The command")
        return (
            f"Your shell tried to run '{cmd}', but could not find an executable "
            "with that name in any folder listed in your system PATH."
        )

    def generate_human_explanation(self, vars: Dict[str, Any]) -> str:
        cmd = vars.get("command", "it")
        return (
            f"Your terminal has no idea what '{cmd}' is.\n"
            "Either it's not installed, or your PATH doesn't know where it lives."
        )

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        cmd = vars.get("command", "command")
        return [
            f"Check for typos: Did you mean another command instead of `{cmd}`?",
            f"Verify if `{cmd}` is installed on your system.",
            "If just installed, restart your terminal to refresh the PATH environment variable.",
            f"If using npm/pip/cargo, install it globally or run via npx (e.g. `npx {cmd}`)."
        ]
