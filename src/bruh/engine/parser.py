"""Output parser, cleaner, noise filter, and intelligent source location extractor."""

import re
import os
from typing import Optional, List, Tuple
from bruh.presentation.ansi import strip_ansi
from bruh.engine.models import SourceLocation

# Regex patterns for various stack trace location formats
PYTHON_TRACE_REGEX = re.compile(r'File "(?P<file>[^"]+)", line (?P<line>\d+)(?:, in (?P<func>.+))?')
NODE_TRACE_REGEX = re.compile(r'at (?:(?P<caller>[^\s(]+) )?\(?(?P<file>(?:[a-zA-Z]:[\\/]|/|[.\w_-]+[\\/]|\[eval\]|repl)[^:)]*):(?P<line>\d+):(?P<col>\d+)\)?')
COMPILER_LOCATION_REGEX = re.compile(r'^(?P<file>(?:[a-zA-Z]:[\\/]|/|[.\w_-]+[\\/])[^:\s]+):(?P<line>\d+)(?::(?P<col>\d+))?', re.MULTILINE)
TS_LOCATION_REGEX = re.compile(r'^(?P<file>(?:[a-zA-Z]:[\\/]|)[^(\r\n]+\.(?:ts|tsx|mts|cts|js|jsx))\((?P<line>\d+),(?P<col>\d+)\):\s*error\s+TS\d+:', re.MULTILINE | re.IGNORECASE)
TS_COLON_REGEX = re.compile(r'^(?P<file>(?:[a-zA-Z]:[\\/]|)[^:\r\n]+\.(?:ts|tsx|mts|cts|js|jsx)):(?P<line>\d+):(?P<col>\d+)\s+-\s+error\s+TS\d+:', re.MULTILINE | re.IGNORECASE)

# Pattern for explicit exception class headers
STRUCTURED_EXCEPTION_REGEX = re.compile(
    r'^(?:(?P<cls>[A-Za-z0-9_.]*(?:Error|Exception|Fault|Panic|Failure)):\s*(?P<msg>[^\n\r]*))',
    re.MULTILINE
)

# Noisy lines to ignore when finding error headlines
NOISE_PATTERNS = [
    re.compile(r"^\[notice\]\s+.*", re.IGNORECASE),
    re.compile(r"^npm\s+(?:notice|timing)\s+.*", re.IGNORECASE),
    re.compile(r"^npm\s+error\s+A complete log of this run can be found in:.*", re.IGNORECASE),
    re.compile(r"^npm\s+error\s+logfile:.*", re.IGNORECASE),
    re.compile(r"^\s*$", re.IGNORECASE),
]

def is_library_or_runtime_frame(file_path: str) -> bool:
    """Determine if a file path belongs to runtime/standard library or installed packages."""
    if not file_path:
        return False
    
    fp_lower = file_path.lower().replace("/", "\\")

    # <string>, <stdin>, [eval] represent direct user commands
    if file_path in ("<string>", "<stdin>", "<string>:1", "<stdin>:1", "[eval]", "repl", "<anonymous>"):
        return False

    # Package managers and node internals
    if "site-packages" in fp_lower or "dist-packages" in fp_lower or "node_modules" in fp_lower or "node:internal" in fp_lower:
        return True

    # Python standard library paths (e.g. \Python312\Lib\socket.py, /usr/lib/python3.x/...)
    if "\\lib\\" in fp_lower or "/lib/" in file_path.lower():
        # Check if it's standard library
        if "python" in fp_lower or "lib\\unittest" in fp_lower or "lib\\socket" in fp_lower or "lib\\http" in fp_lower or "lib\\urllib" in fp_lower or "lib\\json" in fp_lower or "lib\\asyncio" in fp_lower or "lib\\threading" in fp_lower:
            return True

    # Frozen importlib internals
    if "<frozen " in fp_lower:
        return True

    return False

class ErrorParser:
    """Parses, cleans, and extracts structured metadata from raw terminal output."""

    @staticmethod
    def clean_output(raw_output: str) -> str:
        """Strip ANSI escapes, normalize newlines, and filter out noisy package-manager banners."""
        if not raw_output:
            return ""
        cleaned = strip_ansi(raw_output)
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
        return cleaned.strip()

    @staticmethod
    def filter_noise(cleaned_output: str) -> str:
        """Remove pure noise lines (e.g. pip upgrade notices, npm log paths)."""
        if not cleaned_output:
            return ""
        lines = []
        for line in cleaned_output.splitlines():
            if any(p.match(line.strip()) for p in NOISE_PATTERNS if not p.pattern.startswith(r"^\s*$")):
                continue
            lines.append(line)
        return "\n".join(lines).strip()

    @classmethod
    def extract_location(cls, cleaned_output: str) -> Optional[SourceLocation]:
        """Extract the most relevant user source code location from the error output."""
        if not cleaned_output:
            return None

        # 1. Check Python stack traces
        python_matches = list(PYTHON_TRACE_REGEX.finditer(cleaned_output))
        if python_matches:
            user_frames = []
            lib_frames = []

            for m in python_matches:
                f = m.group("file")
                if is_library_or_runtime_frame(f):
                    lib_frames.append(m)
                else:
                    user_frames.append(m)

            # Prefer the most recent user frame (the site where user code triggered the failure)
            chosen = user_frames[-1] if user_frames else lib_frames[-1]

            func_name = chosen.group("func") if chosen.group("func") else None
            return SourceLocation(
                file=chosen.group("file"),
                line=int(chosen.group("line")),
                function=func_name,
                snippet=f"in {func_name}" if func_name and func_name != "<module>" else None
            )

        # 2. Check Node.js stack traces
        node_matches = list(NODE_TRACE_REGEX.finditer(cleaned_output))
        if node_matches:
            user_frames = []
            lib_frames = []

            for match in node_matches:
                f = match.group("file")
                if is_library_or_runtime_frame(f):
                    lib_frames.append(match)
                else:
                    user_frames.append(match)

            if user_frames:
                chosen = user_frames[0]
                caller = chosen.group("caller")
                func_clean = caller if caller and caller not in ("Object.<anonymous>", "Object.eval", "[eval]", "anonymous") else None
                return SourceLocation(
                    file=chosen.group("file"),
                    line=int(chosen.group("line")),
                    column=int(chosen.group("col")),
                    function=func_clean,
                    snippet=f"in {func_clean}" if func_clean else None
                )

        # 3. Check compiler / linter / typescript / node syntax error locations
        ts_match = TS_LOCATION_REGEX.search(cleaned_output)
        if ts_match:
            return SourceLocation(
                file=ts_match.group("file").strip(),
                line=int(ts_match.group("line")),
                column=int(ts_match.group("col"))
            )

        ts_colon_match = TS_COLON_REGEX.search(cleaned_output)
        if ts_colon_match:
            return SourceLocation(
                file=ts_colon_match.group("file").strip(),
                line=int(ts_colon_match.group("line")),
                column=int(ts_colon_match.group("col"))
            )

        comp_match = COMPILER_LOCATION_REGEX.search(cleaned_output)
        if comp_match:
            line_val = int(comp_match.group("line")) if comp_match.group("line") else None
            col_val = int(comp_match.group("col")) if comp_match.group("col") else None
            return SourceLocation(
                file=comp_match.group("file"),
                line=line_val,
                column=col_val
            )

        if node_matches:
            chosen = node_matches[0]
            caller = chosen.group("caller")
            func_clean = caller if caller and caller not in ("Object.<anonymous>", "Object.eval", "[eval]", "anonymous") else None
            return SourceLocation(
                file=chosen.group("file"),
                line=int(chosen.group("line")),
                column=int(chosen.group("col")),
                function=func_clean,
                snippet=f"in {func_clean}" if func_clean else None
            )

        return None

    @classmethod
    def extract_error_type_and_message(cls, cleaned_output: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract explicit error class name and the accompanying message."""
        if not cleaned_output:
            return None, None

        matches = list(STRUCTURED_EXCEPTION_REGEX.finditer(cleaned_output))
        if matches:
            last = matches[-1]
            err_type = last.group("cls").strip()
            err_msg = last.group("msg").strip() if last.group("msg") else None
            return err_type, err_msg

        return None, None

    @classmethod
    def detect_ecosystem(cls, cleaned_output: str, command: Optional[str] = None) -> Optional[str]:
        """Detect language or runtime ecosystem from output signatures and command name."""
        cmd_lower = (command or "").lower()
        out_lower = (cleaned_output or "").lower()

        if "python" in cmd_lower or "pytest" in cmd_lower or "traceback (most recent call last)" in out_lower:
            return "Python"
        if "node" in cmd_lower or "npm" in cmd_lower or "yarn" in cmd_lower or "pnpm" in cmd_lower or "requirestack" in out_lower or "node:internal" in out_lower:
            return "Node.js"
        if "git" in cmd_lower or "fatal: not a git" in out_lower:
            return "Git"
        if "cargo" in cmd_lower or "rustc" in cmd_lower or "can't find crate" in out_lower:
            return "Rust"
        if "go " in cmd_lower or "go run" in cmd_lower:
            return "Go"
        if "pwsh" in cmd_lower or "powershell" in cmd_lower or "commandnotfoundexception" in out_lower:
            return "PowerShell"

        return None

    @classmethod
    def extract_error_headline(cls, cleaned_output: str) -> str:
        """Find the most descriptive single line or summary representing the error, ignoring noise."""
        filtered = cls.filter_noise(cleaned_output)
        if not filtered:
            return ""

        lines = [line.strip() for line in filtered.splitlines() if line.strip()]
        if not lines:
            return ""

        for line in reversed(lines):
            if any(marker in line.lower() for marker in [
                "modulenotfounderror", "cannot find module", "eaddrinuse", "eacces",
                "enoent", "econnrefused", "syntaxerror", "permissionerror",
                "filenotfounderror", "connectionrefusederror", "command not found",
                "is not recognized", "fatal:", "eresolve", "runtimeerror", "typeerror",
                "valueerror", "indexerror", "keyerror", "attributeerror", "bad gateway",
                "gateway timeout", "unauthorized", "forbidden", "timeouterror", "connectionerror"
            ]):
                return line

        matches = list(STRUCTURED_EXCEPTION_REGEX.finditer(filtered))
        if matches:
            return matches[-1].group(0).strip()

        return lines[-1]
