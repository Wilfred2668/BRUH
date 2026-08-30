"""ANSI styling, colors, and box-drawing utilities for Bruh."""

import re
import sys
from bruh.config import is_color_enabled

# ANSI Escape sequence regex
ANSI_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from a string."""
    if not text:
        return ""
    return ANSI_REGEX.sub("", text)

class Style:
    """ANSI color and style constants with auto-disabling support."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright foreground colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

def colorize(text: str, *styles: str) -> str:
    """Apply ANSI styles to text if colors are enabled."""
    if not is_color_enabled() or not styles:
        return text
    prefix = "".join(styles)
    return f"{prefix}{text}{Style.RESET}"

def bold(text: str) -> str:
    return colorize(text, Style.BOLD)

def dim(text: str) -> str:
    return colorize(text, Style.DIM)

def red(text: str) -> str:
    return colorize(text, Style.BRIGHT_RED)

def green(text: str) -> str:
    return colorize(text, Style.BRIGHT_GREEN)

def yellow(text: str) -> str:
    return colorize(text, Style.BRIGHT_YELLOW)

def cyan(text: str) -> str:
    return colorize(text, Style.BRIGHT_CYAN)

def magenta(text: str) -> str:
    return colorize(text, Style.BRIGHT_MAGENTA)

def blue(text: str) -> str:
    return colorize(text, Style.BRIGHT_BLUE)

def code_block(cmd: str) -> str:
    """Format a command line code block."""
    return f"  {colorize('$', Style.DIM)} {bold(cyan(cmd))}"

def can_encode(text: str) -> bool:
    """Check if stdout can encode the given string without error."""
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
        return True
    except Exception:
        return False

def safe_char(unicode_char: str, ascii_fallback: str) -> str:
    """Return the unicode char if terminal supports it, otherwise ascii fallback."""
    return unicode_char if can_encode(unicode_char) else ascii_fallback

def divider(width: int = 60, char: str = "━") -> str:
    """Return a horizontal divider line with automatic ASCII fallback."""
    divider_char = safe_char(char, "=")
    line = divider_char * width
    return colorize(line, Style.DIM, Style.BRIGHT_BLACK)
