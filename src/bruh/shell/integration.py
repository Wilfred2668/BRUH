"""Installer and script generator for Bruh shell integrations."""

import sys
from pathlib import Path
from typing import Optional, Tuple
from bruh.shell.detector import ShellDetector

HOOK_MARKER_START = "# >>> bruh shell integration >>>"
HOOK_MARKER_END = "# <<< bruh shell integration <<<"

SCRIPTS_DIR = Path(__file__).parent / "scripts"

class ShellIntegration:
    """Manages installation, uninstallation, and code generation for shell hooks."""

    @classmethod
    def get_init_script(cls, shell: str) -> str:
        """Return the initialization script for the given shell."""
        shell_lower = shell.lower()
        if "pwsh" in shell_lower or "powershell" in shell_lower:
            script_path = SCRIPTS_DIR / "bruh.ps1"
            if script_path.exists():
                return script_path.read_text(encoding="utf-8")
        elif "zsh" in shell_lower:
            script_path = SCRIPTS_DIR / "bruh.zsh"
            if script_path.exists():
                return script_path.read_text(encoding="utf-8")
        elif "bash" in shell_lower:
            script_path = SCRIPTS_DIR / "bruh.bash"
            if script_path.exists():
                return script_path.read_text(encoding="utf-8")

        return f"# Shell '{shell}' is not currently supported by automatic hook generation."

    @classmethod
    def install(cls, target_shell: Optional[str] = None) -> Tuple[bool, str]:
        """Install shell integration hook into the user's shell profile."""
        detected_shell, profile_path = ShellDetector.detect_shell()
        shell = target_shell or detected_shell

        if shell == "unknown" or not profile_path:
            return False, f"Could not automatically detect a supported shell profile for '{shell}'."

        try:
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            existing_content = ""
            if profile_path.exists():
                existing_content = profile_path.read_text(encoding="utf-8", errors="replace")

            # Always copy the latest hook script into ~/.bruh/
            bruh_dir = Path.home() / ".bruh"
            bruh_dir.mkdir(parents=True, exist_ok=True)

            init_snippet = ""
            if shell == "powershell":
                hook_dest = bruh_dir / "bruh.ps1"
                hook_dest.write_text(cls.get_init_script("powershell"), encoding="utf-8")
                init_snippet = f"\n{HOOK_MARKER_START}\n. \"$HOME\\.bruh\\bruh.ps1\"\n{HOOK_MARKER_END}\n"
            elif shell == "zsh":
                hook_dest = bruh_dir / "bruh.zsh"
                hook_dest.write_text(cls.get_init_script("zsh"), encoding="utf-8")
                init_snippet = f"\n{HOOK_MARKER_START}\nsource \"$HOME/.bruh/bruh.zsh\"\n{HOOK_MARKER_END}\n"
            elif shell == "bash":
                hook_dest = bruh_dir / "bruh.bash"
                hook_dest.write_text(cls.get_init_script("bash"), encoding="utf-8")
                init_snippet = f"\n{HOOK_MARKER_START}\nsource \"$HOME/.bruh/bruh.bash\"\n{HOOK_MARKER_END}\n"

            if HOOK_MARKER_START in existing_content:
                # Update existing block
                lines = existing_content.splitlines(keepends=True)
                new_lines = []
                skipping = False
                for line in lines:
                    if HOOK_MARKER_START in line:
                        skipping = True
                        continue
                    if HOOK_MARKER_END in line:
                        skipping = False
                        continue
                    if not skipping:
                        new_lines.append(line)
                existing_content = "".join(new_lines).rstrip() + "\n"

            with open(profile_path, "w", encoding="utf-8") as f:
                f.write(existing_content + init_snippet)

            return True, f"Successfully installed Bruh hook into {profile_path}"
        except Exception as e:
            return False, f"Failed to write to {profile_path}: {e}"

    @classmethod
    def uninstall(cls, target_shell: Optional[str] = None) -> Tuple[bool, str]:
        """Remove shell integration hook from the user's shell profile."""
        detected_shell, profile_path = ShellDetector.detect_shell()
        shell = target_shell or detected_shell

        if not profile_path or not profile_path.exists():
            return True, "No profile file found to clean."

        try:
            content = profile_path.read_text(encoding="utf-8", errors="replace")
            if HOOK_MARKER_START not in content:
                return True, "Bruh integration hook was not found in profile."

            # Strip out lines between markers
            lines = content.splitlines(keepends=True)
            new_lines = []
            skipping = False
            for line in lines:
                if HOOK_MARKER_START in line:
                    skipping = True
                    continue
                if HOOK_MARKER_END in line:
                    skipping = False
                    continue
                if not skipping:
                    new_lines.append(line)

            profile_path.write_text("".join(new_lines), encoding="utf-8")
            return True, f"Successfully removed Bruh hook from {profile_path}"
        except Exception as e:
            return False, f"Failed to modify {profile_path}: {e}"
