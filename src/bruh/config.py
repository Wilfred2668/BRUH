"""Configuration and path management for Bruh."""

import os
from pathlib import Path

# Base configuration directory in the user's home
BRUH_DIR = Path(os.environ.get("BRUH_HOME", Path.home() / ".bruh"))
SESSIONS_DIR = BRUH_DIR / "sessions"
LAST_SESSION_FILE = BRUH_DIR / "last_session.json"
CONFIG_FILE = BRUH_DIR / "config.json"

# Environment variables
ENV_NO_COLOR = "NO_COLOR"
ENV_BRUH_NO_COLOR = "BRUH_NO_COLOR"
ENV_BRUH_DEBUG = "BRUH_DEBUG"
ENV_BRUH_FORCE_COLOR = "BRUH_FORCE_COLOR"

def ensure_bruh_dir() -> Path:
    """Ensure the .bruh directory and subdirectories exist with proper permissions."""
    BRUH_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return BRUH_DIR

def is_debug() -> bool:
    """Return True if debug mode is enabled."""
    return os.environ.get(ENV_BRUH_DEBUG, "").lower() in ("1", "true", "yes")

def is_color_enabled() -> bool:
    """Determine whether terminal color should be used."""
    if os.environ.get(ENV_BRUH_FORCE_COLOR, "").lower() in ("1", "true", "yes"):
        return True
    if os.environ.get(ENV_NO_COLOR) or os.environ.get(ENV_BRUH_NO_COLOR):
        return False
    # Check if stdout is attached to a terminal
    try:
        import sys
        return sys.stdout.isatty()
    except Exception:
        return True
