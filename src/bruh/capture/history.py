"""Shell history reader fallback with parent shell detection, multiline reconstruction, boundary isolation, and freshness checks."""

import os
import sys
import time
from pathlib import Path
from typing import Optional, List, Tuple

def get_parent_process_name() -> str:
    """Detect the name of the parent shell process."""
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32
            TH32CS_SNAPPROCESS = 0x00000002
            class PROCESSENTRY32(ctypes.Structure):
                _fields_ = [
                    ("dwSize", wintypes.DWORD),
                    ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_void_p),
                    ("th32ModuleID", wintypes.DWORD),
                    ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD),
                    ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", wintypes.DWORD),
                    ("szExeFile", ctypes.c_char * 260)
                ]
            hSnap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            pe = PROCESSENTRY32()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
            parent_pid = os.getppid()
            parent_exe = "unknown"
            if kernel32.Process32First(hSnap, ctypes.byref(pe)):
                while True:
                    if pe.th32ProcessID == parent_pid:
                        parent_exe = pe.szExeFile.decode("utf-8", errors="ignore").lower()
                        break
                    if not kernel32.Process32Next(hSnap, ctypes.byref(pe)):
                        break
            kernel32.CloseHandle(hSnap)
            return parent_exe
        except Exception:
            return "unknown"
    else:
        try:
            ppid = os.getppid()
            comm_path = Path(f"/proc/{ppid}/comm")
            if comm_path.exists():
                return comm_path.read_text(encoding="utf-8").strip().lower()
        except Exception:
            pass
    return "unknown"

def is_multiline_fragment(cmd: str) -> bool:
    """Check if a single command string is an unparseable fragment of a multiline block."""
    if not cmd:
        return False
    trimmed = cmd.strip()
    
    # If it is a complete, closed here-string, it is NOT an incomplete fragment
    if (trimmed.startswith('@"') and '"@' in trimmed[2:]) or (trimmed.startswith("@'") and "'@" in trimmed[2:]):
        return False

    # Here-string closing tags alone without the opening tag
    if trimmed.startswith('"@') or trimmed.startswith("'@"):
        return True
    # Dangling pipe or operator
    if trimmed.startswith("|") or trimmed.startswith("&&") or trimmed.startswith("||"):
        return True
    return False

def isolate_command_before_bruh(raw_cmd: str) -> Optional[str]:
    """Extract the last non-bruh command from a potentially combined or multiline pasted block."""
    if not raw_cmd:
        return None

    raw_clean = raw_cmd.strip()
    if not raw_clean:
        return None

    # Handle pasted multiple commands ending with bruh
    lines = [l.strip() for l in raw_clean.splitlines() if l.strip()]
    if not lines:
        return None

    # Filter out lines that are bruh, clear, cls
    non_bruh_lines = []
    for line in lines:
        if line.startswith(": ") and ";" in line:
            line = line.split(";", 1)[1].strip()
        # Strip trailing PowerShell line continuation backtick
        line = line.rstrip("`").strip()
        if line.startswith("bruh") or line == "clear" or line == "cls":
            continue
        if line:
            non_bruh_lines.append(line)

    if not non_bruh_lines:
        return None

    # If the first line starts a here-string
    if non_bruh_lines[0].startswith('@"') or non_bruh_lines[0].startswith("@'"):
        close_tag = '"@' if non_bruh_lines[0].startswith('@"') else "'@"
        close_idx = -1
        for idx, l in enumerate(non_bruh_lines):
            if l.startswith(close_tag):
                close_idx = idx
                break
        
        # If there are commands after the here-string closed, take the last command
        if close_idx != -1 and close_idx < len(non_bruh_lines) - 1:
            return non_bruh_lines[-1]
        
        # Otherwise the full here-string is the target
        return "\n".join(non_bruh_lines)

    target = non_bruh_lines[-1]
    # Strip any trailing PowerShell line continuation backtick
    target = target.rstrip("`").strip()
    return target

def reconstruct_multiline(lines: List[str], end_idx: int) -> str:
    """Attempt to reconstruct a full multiline statement from history lines."""
    target = lines[end_idx].strip()
    if target.startswith('"@') or target.startswith("'@"):
        delimiter = '@"' if target.startswith('"@') else "@'"
        # Scan upwards for matching opening delimiter
        for start_idx in range(end_idx - 1, max(-1, end_idx - 50), -1):
            line_trim = lines[start_idx].strip()
            if line_trim == delimiter or line_trim.startswith(delimiter) or line_trim.endswith(delimiter):
                # Join lines into one block
                combined = "\n".join(lines[start_idx:end_idx + 1])
                return combined.strip()
    return target

def get_history_file_paths_for_shell(parent_shell: str) -> List[Path]:
    """Return possible shell history file paths filtered by the active parent shell."""
    paths = []
    
    # PowerShell (only if parent is PowerShell / pwsh / Windows Terminal)
    if "powershell" in parent_shell or "pwsh" in parent_shell or "windowsterminal" in parent_shell:
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA")
            if appdata:
                paths.append(Path(appdata) / "Microsoft" / "Windows" / "PowerShell" / "PSReadLine" / "ConsoleHost_history.txt")
            paths.append(Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "PowerShell" / "PSReadLine" / "ConsoleHost_history.txt")
        paths.append(Path.home() / ".local" / "share" / "powershell" / "PSReadLine" / "ConsoleHost_history.txt")

    # Zsh
    if "zsh" in parent_shell:
        zdotdir = os.environ.get("ZDOTDIR")
        if zdotdir:
            paths.append(Path(zdotdir) / ".zsh_history")
        paths.append(Path.home() / ".zsh_history")
        paths.append(Path.home() / ".zhistory")

    # Bash
    if "bash" in parent_shell:
        histfile = os.environ.get("HISTFILE")
        if histfile:
            paths.append(Path(histfile))
        paths.append(Path.home() / ".bash_history")

    # Generic fallback only if shell is unknown
    if parent_shell == "unknown":
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA")
            if appdata:
                paths.append(Path(appdata) / "Microsoft" / "Windows" / "PowerShell" / "PSReadLine" / "ConsoleHost_history.txt")
        paths.append(Path.home() / ".bash_history")
        paths.append(Path.home() / ".zsh_history")

    return paths

def get_last_command_from_history(max_age_seconds: float = 300.0) -> Tuple[Optional[str], float]:
    """Find the most recent non-bruh command from the active shell history file.
    
    Returns (command_str, file_mtime).
    """
    parent_shell = get_parent_process_name()

    # In CMD, PSReadLine does not apply
    if "cmd.exe" in parent_shell or parent_shell == "cmd":
        return None, 0.0

    now = time.time()
    for hist_path in get_history_file_paths_for_shell(parent_shell):
        try:
            if hist_path.exists():
                mtime = hist_path.stat().st_mtime
                if (now - mtime) > max_age_seconds:
                    continue

                with open(hist_path, "r", encoding="utf-8", errors="replace") as f:
                    raw_lines = [l.rstrip("\r\n") for l in f.readlines()]
                
                for idx in range(len(raw_lines) - 1, -1, -1):
                    line = raw_lines[idx]
                    trimmed = line.strip()
                    if trimmed.startswith(": ") and ";" in trimmed:
                        trimmed = trimmed.split(";", 1)[1].strip()
                    
                    if trimmed and not trimmed.startswith("bruh") and not trimmed.startswith("clear") and not trimmed.startswith("cls"):
                        full_cmd = reconstruct_multiline(raw_lines, idx)
                        clean_cmd = isolate_command_before_bruh(full_cmd)
                        if clean_cmd:
                            return clean_cmd, mtime
        except Exception:
            continue

    return None, 0.0
