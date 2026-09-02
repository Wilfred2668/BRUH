"""Bruh test suite."""

import sys
from pathlib import Path

# Add src/ to sys.path so tests can run without needing prior installation
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

