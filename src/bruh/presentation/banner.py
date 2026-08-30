"""ASCII branding and setup banners for Bruh."""

from bruh.presentation.ansi import (
    colorize, bold, dim, cyan, green, red, yellow, magenta, divider, Style
)
from bruh.personality.phrases import WELCOME_SUBTITLE, SETUP_FEATURES

BRUH_ASCII = r"""
   ██████╗ ██████╗ ██╗   ██╗██╗  ██╗
   ██╔══██╗██╔══██╗██║   ██║██║  ██║
   ██████╔╝██████╔╝██║   ██║███████║
   ██╔══██╗██╔══██╗██║   ██║██╔══██║
   ██████╔╝██║  ██║╚██████╔╝██║  ██║
   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝
"""

def render_welcome_screen(detected_shell: str) -> str:
    """Render the polished first-run welcome banner."""
    lines = []
    lines.append(divider(62))
    lines.append("")
    for ascii_line in BRUH_ASCII.strip("\n").splitlines():
        lines.append(colorize(ascii_line, Style.BOLD, Style.BRIGHT_CYAN))
    lines.append("")
    lines.append(f"   {bold('Welcome to Bruh.')}")
    lines.append("")
    lines.append(f"   {dim(WELCOME_SUBTITLE)}")
    lines.append("")
    for feature in SETUP_FEATURES:
        lines.append(f"   {green(feature)}")
    lines.append("")
    lines.append(f"   Detected shell: {bold(cyan(detected_shell))}")
    lines.append("")
    lines.append(divider(62))
    return "\n".join(lines)

def render_ready_screen() -> str:
    """Render the post-setup completion banner."""
    lines = []
    lines.append(divider(62))
    lines.append("")
    lines.append(f"   {bold(green('✓ BRUH IS READY'))}")
    lines.append("")
    lines.append("   Run commands normally:")
    lines.append("")
    lines.append(f"       {cyan('npm run dev')}")
    lines.append("")
    lines.append("   If something explodes, just type:")
    lines.append("")
    lines.append(f"       {bold(magenta('bruh'))}")
    lines.append("")
    lines.append("   I'll explain what happened.")
    lines.append("")
    lines.append(divider(62))
    return "\n".join(lines)
