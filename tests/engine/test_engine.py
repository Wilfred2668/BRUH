"""Unit tests for the DiagnosticEngine, Matcher, and Rule Registry."""

import unittest
from bruh.engine.matcher import DiagnosticEngine
from bruh.engine.registry import RuleRegistry
from bruh.rules.base import BaseDiagnosticRule
from bruh.engine.models import RuleMatch
from tests.fixtures import sample_errors

class TestDiagnosticEngine(unittest.TestCase):

    def setUp(self):
        self.engine = DiagnosticEngine()

    def test_diagnose_known_error_module_not_found(self):
        result = self.engine.diagnose(sample_errors.PYTHON_MODULE_NOT_FOUND_PANDAS, command="python app.py")
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "module-not-found")
        self.assertIn("pandas", result.explanation)
        self.assertIsNotNone(result.location)
        self.assertEqual(result.location.file, "app.py")
        self.assertEqual(result.location.line, 15)
        self.assertIn("pandas", result.get_var("module"))

    def test_diagnose_unknown_error_no_hallucination(self):
        result = self.engine.diagnose(sample_errors.UNKNOWN_EXOTIC_ERROR, command="./boot")
        self.assertFalse(result.is_known)
        self.assertEqual(result.rule_id, "unknown")
        self.assertIn("KernelPanicException", result.original_error)
        self.assertGreaterEqual(len(result.suggestions), 1)

    def test_silent_failure_handling(self):
        result = self.engine.diagnose("", command="./silent_crash", exit_code=139)
        self.assertFalse(result.is_known)
        self.assertEqual(result.rule_id, "no-output")
        self.assertIn("silent", result.explanation.lower())

    def test_custom_rule_registration(self):
        registry = RuleRegistry(load_defaults=False)

        class CustomCoffeeRule(BaseDiagnosticRule):
            rule_id = "coffee-spilled"
            name = "Coffee Spilled Error"
            priority = 200

            def match(self, cleaned_output, command=None, exit_code=None):
                if "418 I'm a teapot" in cleaned_output:
                    return RuleMatch(
                        matched=True,
                        title="💀 Teapot Error 418",
                        extracted_vars={"beverage": "coffee"}
                    )
                return None

        registry.register(CustomCoffeeRule())
        custom_engine = DiagnosticEngine(registry=registry)

        result = custom_engine.diagnose("HTTP/1.1 418 I'm a teapot")
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "coffee-spilled")

if __name__ == "__main__":
    unittest.main()
