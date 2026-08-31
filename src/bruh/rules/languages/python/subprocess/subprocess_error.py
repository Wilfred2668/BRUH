"""Diagnostic rule for subprocess and external process failures."""

import re
import ast
from typing import Dict, Any, List, Optional
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch

SUBPROCESS_ERR_REGEX = re.compile(
    r"(?:(?:subprocess\.CalledProcessError:\s*Command\s+(?P<cmd_raw>.+?)\s+returned non-zero exit status\s+(?P<code>\d+)\.?)|"
    r"(?:subprocess\.TimeoutExpired:\s*Command\s+(?P<t_cmd_raw>.+?)\s+timed out after\s+(?P<secs>[^\s]+)\s+seconds))",
    re.IGNORECASE
)

def _clean_subprocess_command(raw_cmd: str) -> str:
    """Format extracted command string cleanly from shell string or list representation."""
    if not raw_cmd:
        return "command"
    c = raw_cmd.strip()
    if (c.startswith("'[") and c.endswith("]'")) or (c.startswith('"[') and c.endswith(']"')):
        c = c[1:-1]
    if c.startswith("[") and c.endswith("]"):
        try:
            parsed = ast.literal_eval(c)
            if isinstance(parsed, list):
                return " ".join(str(item) for item in parsed)
        except Exception:
            return c.strip("[]'\" ")
    return c.strip("'\"")

class SubprocessErrorRule(BaseDiagnosticRule):
    """Diagnoses subprocess execution and child process lifecycle failures."""

    rule_id = "subprocess-error"
    name = "Subprocess Execution Failure"
    category = "runtime"
    priority = 77

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        if exit_code == 0:
            return None

        match = SUBPROCESS_ERR_REGEX.search(cleaned_output)
        if match:
            raw_err = match.group(0).strip()
            raw_cmd = match.group("cmd_raw") or match.group("t_cmd_raw")
            cmd_name = _clean_subprocess_command(raw_cmd)
            code = match.group("code")
            secs = match.group("secs")

            if secs:
                title = f"💀 subprocess.TimeoutExpired: '{cmd_name}' (after {secs}s)"
                kind = "timeout"
            else:
                title = f"💀 subprocess.CalledProcessError: '{cmd_name}' (exit code {code})"
                kind = "exit_error"

            return RuleMatch(
                matched=True,
                title=title,
                original_error=raw_err,
                extracted_vars={
                    "cmd": cmd_name,
                    "code": code,
                    "secs": secs,
                    "kind": kind,
                    "raw": raw_err
                }
            )

        return None

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        cmd = vars.get("cmd", "command")
        code = vars.get("code")
        secs = vars.get("secs")
        kind = vars.get("kind")

        if kind == "timeout":
            return f"A child process executed via Python's subprocess module ('{cmd}') failed to complete within the configured timeout limit ({secs}s)."
        
        return f"A child process executed via Python's subprocess module ('{cmd}') exited with a non-zero failure code ({code})."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        cmd = vars.get("cmd", "command")
        kind = vars.get("kind")

        if kind == "timeout":
            return [
                f"Increase the timeout parameter passed to `subprocess.run(..., timeout=...)`.",
                f"Run '{cmd}' directly in your terminal to see if it is hanging or waiting for user input.",
                "Ensure the child process does not block on unbuffered stdin or stdout."
            ]

        return [
            f"Run '{cmd}' manually in your terminal to inspect its full error output and stderr.",
            "Capture stderr in your code using `subprocess.run(..., capture_output=True, text=True)` to inspect error messages.",
            "Wrap the call in `try/except subprocess.CalledProcessError` to handle non-zero exit codes gracefully."
        ]
