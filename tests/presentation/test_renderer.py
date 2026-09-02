"""Unit tests for the TerminalRenderer and presentation components."""

import unittest
import os
from bruh.engine.models import DiagnosticResult, SourceLocation
from bruh.presentation.renderer import TerminalRenderer
from bruh.presentation.ansi import strip_ansi

class TestTerminalRenderer(unittest.TestCase):

    def test_render_known_diagnostic(self):
        result = DiagnosticResult(
            is_known=True,
            rule_id="module-not-found",
            title="💀 ModuleNotFoundError",
            original_error="No module named 'pandas'",
            location=SourceLocation(file="app.py", line=15),
            explanation="Python tried to import 'pandas', but it isn't available.",
            human_explanation="Your code wants pandas. Your environment said: 'I don't know her.'",
            suggestions=[
                "Check if pandas is installed: `pip show pandas`",
                "Install it: `pip install pandas`"
            ]
        )

        rendered = TerminalRenderer.render(result)
        plain = strip_ansi(rendered)

        self.assertIn("BRUH", plain)
        self.assertIn("ModuleNotFoundError", plain)
        self.assertIn("app.py:15", plain)
        self.assertIn("Bruh, what happened?", plain)
        self.assertIn("Try this", plain)
        self.assertIn("pip install pandas", plain)

    def test_render_unknown_diagnostic(self):
        result = DiagnosticResult(
            is_known=False,
            rule_id="unknown",
            title="💀 UnknownCompilerPanic",
            original_error="Unknown internal compiler error",
            location=SourceLocation(file="main.rs", line=40),
            explanation="I can identify some information from this error, but I don't have a reliable diagnosis for it yet.",
            suggestions=["Check documentation."]
        )

        rendered = TerminalRenderer.render(result)
        plain = strip_ansi(rendered)

        self.assertIn("BRUH", plain)
        self.assertIn("I don't recognize this error yet", plain)
        self.assertIn("main.rs:40", plain)
        self.assertIn("Try this", plain)

    def test_rendering_no_color_environment(self):
        os.environ["NO_COLOR"] = "1"
        try:
            result = DiagnosticResult(
                is_known=True,
                title="💀 Test Error",
                explanation="Test explanation."
            )
            rendered = TerminalRenderer.render(result)
            self.assertEqual(rendered, strip_ansi(rendered))
        finally:
            os.environ.pop("NO_COLOR", None)

if __name__ == "__main__":
    unittest.main()
