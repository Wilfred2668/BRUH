"""Terminal output renderer with unified layout, clean spacing, and modern CLI aesthetics."""

import re
import textwrap
from typing import List, Optional
from bruh.engine.models import DiagnosticResult
from bruh.presentation.ansi import (
    colorize, bold, dim, cyan, green, red, yellow, magenta, divider, code_block, Style
)
from bruh.personality.phrases import (
    TITLE_BRAND,
    TITLE_UNKNOWN,
    TITLE_WHERE,
    TITLE_WHAT_HAPPENED,
    TITLE_TRY_THIS,
    NO_ERROR_DETECTED_TITLE,
    NO_ERROR_DETECTED_MESSAGE
)

def format_multiline(text: str, indent: str = "   ", width: int = 68) -> str:
    """Format multiline text with consistent indentation and text wrapping."""
    if not text:
        return ""
    lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip():
            wrapped = textwrap.fill(
                paragraph.strip(),
                width=width,
                initial_indent=indent,
                subsequent_indent=indent
            )
            lines.append(wrapped)
        else:
            lines.append("")
    return "\n".join(lines)

class TerminalRenderer:
    """Renders DiagnosticResult objects into a strictly unified terminal layout."""

    @classmethod
    def render(cls, result: DiagnosticResult, width: int = 68) -> str:
        """Render a full diagnostic result according to the unified output contract."""
        lines = []
        div = divider(width)
        lines.append(div)
        lines.append("")

        # 1. Centered Brand Header
        brand = bold(cyan(TITLE_BRAND))
        lines.append(f"{brand:^{width + 8}}")
        lines.append("")

        # 2. Status Title
        if result.is_known:
            title_text = result.title if result.title.startswith("💀") else f"💀 {result.title}"
            lines.append(bold(red(title_text)))
        else:
            lines.append(bold(yellow(TITLE_UNKNOWN)))
        lines.append("")

        # 3. Error Message / Headline
        err_msg = result.original_error or result.error_message or ""
        if err_msg and err_msg != result.title:
            lines.append(dim(format_multiline(err_msg, indent="   ", width=width)))
            lines.append("")

        # 4. Where (Source Location) - optional if available
        if result.location:
            lines.append(bold(yellow(TITLE_WHERE)))
            lines.append(f"   {cyan(str(result.location))}")
            if result.location.snippet:
                lines.append(f"   {dim(result.location.snippet)}")
            lines.append("")

        # 5. Bruh, what happened?
        if result.explanation:
            lines.append(bold(magenta(TITLE_WHAT_HAPPENED)))
            lines.append("")
            lines.append(format_multiline(result.explanation, indent="   ", width=width))
            lines.append("")

        # 6. Try This
        if result.suggestions:
            lines.append(bold(cyan(TITLE_TRY_THIS)))
            lines.append("")
            lines.extend(cls._format_suggestions(result.suggestions, width=width))
            lines.append("")

        lines.append(div)
        return "\n".join(lines)

    @classmethod
    def render_success(cls, command: str = "", width: int = 68) -> str:
        """Render the friendly success banner when the last command succeeded."""
        lines = []
        div = divider(width)
        lines.append(div)
        lines.append("")
        brand = bold(cyan(TITLE_BRAND))
        lines.append(f"{brand:^{width + 8}}")
        lines.append("")
        lines.append(f"   {bold(green(NO_ERROR_DETECTED_TITLE))}")
        lines.append("")
        for msg_line in NO_ERROR_DETECTED_MESSAGE.splitlines():
            lines.append(f"   {msg_line}")
        if command:
            lines.append("")
            lines.append(f"   Last command: {dim(command)}")
        lines.append("")
        lines.append(div)
        return "\n".join(lines)

    @classmethod
    def render_unreliable_capture(cls, command: str = "", width: int = 68) -> str:
        """Render notice when an interactive/multiline command could not be safely isolated."""
        lines = []
        div = divider(width)
        lines.append(div)
        lines.append("")
        brand = bold(cyan(TITLE_BRAND))
        lines.append(f"{brand:^{width + 8}}")
        lines.append("")
        msg = bold(yellow("⚠️  Bruh couldn't capture the previous command reliably."))
        lines.append(f"   {msg}")
        lines.append("")
        lines.append("   The previous command appeared to be a multiline or interactive block.")
        lines.append("   To diagnose this failure, pipe the command or pass the error directly:")
        lines.append("")
        lines.append("      bruh explain \"<error message>\"")
        lines.append("")
        lines.append(div)
        return "\n".join(lines)

    @classmethod
    def _format_suggestions(cls, suggestions: List[str], width: int = 68) -> List[str]:
        """Format numbered suggestions and highlight commands."""
        formatted = []
        step_num = 1
        for item in suggestions:
            if item.strip().startswith("- "):
                formatted.append(f"     {item.strip()}")
            elif item.strip().startswith("$ ") or item.strip().startswith("`"):
                clean_cmd = item.strip().lstrip("$ `").rstrip("`")
                formatted.append(f"      {code_block(clean_cmd)}")
            else:
                highlighted = re.sub(
                    r"`([^`]+)`",
                    lambda m: bold(cyan(m.group(1))),
                    item
                )
                wrapped = textwrap.fill(
                    f"{step_num}. {highlighted}",
                    width=width,
                    initial_indent="   ",
                    subsequent_indent="      "
                )
                formatted.append(wrapped)
                step_num += 1
        return formatted
