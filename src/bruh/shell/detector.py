"""Shell detection and environment inspection for Bruh."""

import os
import sys
from pathlib import Path
from typing import Tuple, Optional

class ShellDetector:
    """Detects active shell and locates appropriate shell profile configuration paths."""

    @classmethod
    def detect_shell(cls) -> Tuple[str, Optional[Path]]:
        """Detect the user's shell name ('powershell', 'bash', 'zsh', etc.) and its profile path."""
        # Check explicit environment variables
        shell_env = os.environ.get("SHELL", "")
        ps_module_path = os.environ.get("PSModulePath", "")
        windir = os.environ.get("WINDIR", "")

        # 1. Check if running inside PowerShell
        # On Windows or Linux/macOS with pwsh
        if "pwsh" in shell_env or "powershell" in shell_env:
            return "powershell", cls.get_powershell_profile()

        # If on Windows, default interactive shell is typically PowerShell
        if sys.platform == "win32":
            # Check parent process or standard PS profile
            ps_profile = cls.get_powershell_profile()
            return "powershell", ps_profile

        # 2. Check Zsh
        if "zsh" in shell_env:
            zshrc = Path.home() / ".zshrc"
            return "zsh", zshrc

        # 3. Check Bash
        if "bash" in shell_env:
            bashrc = Path.home() / ".bashrc"
            if not bashrc.exists() and (Path.home() / ".bash_profile").exists():
                bashrc = Path.home() / ".bash_profile"
            return "bash", bashrc

        # 4. Fallback for Unix
        if (Path.home() / ".zshrc").exists():
            return "zsh", Path.home() / ".zshrc"
        elif (Path.home() / ".bashrc").exists():
            return "bash", Path.home() / ".bashrc"

        return "unknown", None

    @classmethod
    def get_powershell_profile(cls) -> Path:
        """Locate the current user's PowerShell profile path."""
        if sys.platform == "win32":
            # Windows PowerShell: Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1
            # PowerShell 7+: Documents\PowerShell\Microsoft.PowerShell_profile.ps1
            docs_dir = Path.home() / "Documents"
            pwsh_7_profile = docs_dir / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
            win_ps_profile = docs_dir / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1"

            if pwsh_7_profile.exists():
                return pwsh_7_profile
            return win_ps_profile
        else:
            # macOS / Linux PowerShell Core
            return Path.home() / ".config" / "powershell" / "Microsoft.PowerShell_profile.ps1"
