"""Base class for diagnostic rules."""

from typing import Dict, Any, List, Optional
import re
from bruh.engine.models import RuleMatch, SourceLocation

class BaseDiagnosticRule:
    """Abstract base class for all reusable diagnostic pattern rules."""

    rule_id: str = "base-rule"
    name: str = "Base Rule"
    category: str = "general"
    priority: int = 100  # Default priority (higher evaluates first)

    def match(
        self,
        cleaned_output: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None
    ) -> Optional[RuleMatch]:
        """Evaluate the rule against the error output and context.
        
        Returns a RuleMatch if recognized, or None if no match.
        """
        raise NotImplementedError("Rules must implement match()")

    def generate_explanation(self, vars: Dict[str, Any]) -> str:
        """Generate a concise, technically accurate explanation."""
        return "An error occurred during execution."

    def generate_human_explanation(self, vars: Dict[str, Any]) -> str:
        """Generate a friendly, plain-English explanation or metaphor."""
        return "Something went wrong while running your command."

    def generate_suggestions(self, vars: Dict[str, Any]) -> List[str]:
        """Generate actionable 'Try this' steps."""
        return ["Check the error message above for details."]
