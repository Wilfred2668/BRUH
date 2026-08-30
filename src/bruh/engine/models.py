"""Core data models for Bruh's diagnostic engine and rules."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class SourceLocation:
    """Represents a code or file location extracted from stack traces or compiler logs."""
    file: str
    line: Optional[int] = None
    column: Optional[int] = None
    snippet: Optional[str] = None
    function: Optional[str] = None

    def __str__(self) -> str:
        loc = self.file
        if self.line is not None:
            loc += f":{self.line}"
            if self.column is not None:
                loc += f":{self.column}"
        return loc

@dataclass
class DiagnosticResult:
    """The normalized diagnostic output produced by matching a rule against error output."""
    is_known: bool = True
    rule_id: str = "unknown"
    category: str = "general"
    title: str = "Error"
    original_error: str = ""
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    ecosystem: Optional[str] = None
    location: Optional[SourceLocation] = None
    explanation: str = ""
    human_explanation: str = ""
    suggestions: List[str] = field(default_factory=list)
    extracted_facts: List[str] = field(default_factory=list)
    extracted_vars: Dict[str, Any] = field(default_factory=dict)
    command: Optional[str] = None
    exit_code: Optional[int] = None

    def get_var(self, key: str, default: Any = "") -> Any:
        return self.extracted_vars.get(key, default)

@dataclass
class RuleMatch:
    """Result of matching a single rule's patterns against an error context."""
    matched: bool
    title: Optional[str] = None
    original_error: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    extracted_vars: Dict[str, Any] = field(default_factory=dict)
    location: Optional[SourceLocation] = None
    custom_explanation: Optional[str] = None
    custom_human_explanation: Optional[str] = None
    custom_suggestions: Optional[List[str]] = None
