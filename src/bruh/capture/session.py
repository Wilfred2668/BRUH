"""Local session capture store for Bruh."""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional
from bruh.config import ensure_bruh_dir, LAST_SESSION_FILE
from bruh.capture.context import CommandContext

class SessionStore:
    """Manages reading and atomic writing of local command diagnostic sessions."""

    def __init__(self, session_file: Optional[Path] = None):
        self.session_file = session_file or LAST_SESSION_FILE

    def save(self, context: CommandContext) -> bool:
        """Atomically write the command context to the session file."""
        try:
            ensure_bruh_dir()
            data = context.to_dict()
            json_str = json.dumps(data, indent=2)

            target_dir = self.session_file.parent
            target_dir.mkdir(parents=True, exist_ok=True)

            # Write to a temporary file in the same directory then replace atomically
            temp_fd, temp_path = tempfile.mkstemp(dir=target_dir, prefix="bruh_session_", suffix=".tmp")
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                f.write(json_str)

            # Set restrictive file permissions (user only read/write) if supported
            try:
                os.chmod(temp_path, 0o600)
            except Exception:
                pass

            # Atomic replace
            os.replace(temp_path, self.session_file)
            return True
        except Exception:
            return False

    def load(self) -> Optional[CommandContext]:
        """Read the most recent command context from the session file."""
        if not self.session_file.exists():
            return None
        try:
            with open(self.session_file, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
            return CommandContext.from_dict(data)
        except Exception:
            # Corrupted or unreadable session file
            return None

    def clear(self) -> bool:
        """Remove the session file."""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
            return True
        except Exception:
            return False
