"""Command execution context data model."""

import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

@dataclass
class CommandContext:
    """Represents captured information about the most recently executed terminal command."""
    command: str = ""
    exit_code: int = 1
    output: str = ""
    cwd: str = ""
    timestamp: float = 0.0
    shell: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommandContext":
        return cls(
            command=data.get("command", ""),
            exit_code=int(data.get("exit_code", 1)),
            output=data.get("output", ""),
            cwd=data.get("cwd", ""),
            timestamp=float(data.get("timestamp", 0.0)),
            shell=data.get("shell", "")
        )
