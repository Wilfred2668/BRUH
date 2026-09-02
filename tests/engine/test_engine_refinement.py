"""Comprehensive tests for Phase 5 Rule Engine Finalization & Robustness."""

import unittest
from pathlib import Path
from bruh.engine.matcher import DiagnosticEngine
from bruh.engine.registry import get_default_registry
from bruh.engine.parser import ErrorParser
from bruh.engine.models import SourceLocation

class TestEngineRefinement(unittest.TestCase):

    def setUp(self):
        self.engine = DiagnosticEngine(registry=get_default_registry())

    # =========================================================================
    # 1. Rule Priority & Conflict Resolution
    # =========================================================================
    def test_priority_tier_order(self):
        """Verify registry rules strictly adhere to priority tier descending sort."""
        rules = self.engine.registry.all_rules()
        priorities = [r.priority for r in rules]
        self.assertEqual(priorities, sorted(priorities, reverse=True))

    def test_module_not_found_wins_over_import_error(self):
        raw = "ModuleNotFoundError: No module named 'django.core'"
        res = self.engine.diagnose(raw, command="python manage.py", exit_code=1)
        self.assertEqual(res.rule_id, "module-not-found")
        self.assertIn("Module not found", res.title)

    def test_import_error_wins_over_generic(self):
        raw = "ImportError: cannot import name 'render' from 'django.shortcuts'"
        res = self.engine.diagnose(raw, command="python views.py", exit_code=1)
        self.assertEqual(res.rule_id, "import-error")
        self.assertIn("render", res.title)
        self.assertIn("django.shortcuts", res.title)

    def test_json_decode_wins_over_syntax_error(self):
        raw = "json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)"
        res = self.engine.diagnose(raw, command="python parse.py", exit_code=1)
        self.assertEqual(res.rule_id, "json-decode-error")

    def test_database_error_wins_over_connection_refused(self):
        raw = "psycopg2.OperationalError: password authentication failed for user \"postgres\""
        res = self.engine.diagnose(raw, command="python db.py", exit_code=1)
        self.assertEqual(res.rule_id, "database-error")
        self.assertIn("Authentication Failed", res.title)

    # =========================================================================
    # 2. Robust Fact & Source Location Extraction
    # =========================================================================
    def test_extract_windows_path_traceback(self):
        raw = 'Traceback (most recent call last):\n  File "C:\\Users\\Admin\\Projects\\backend\\server.py", line 88, in start_app\nValueError: invalid port'
        loc = ErrorParser.extract_location(raw)
        self.assertIsNotNone(loc)
        self.assertIn("server.py", loc.file)
        self.assertEqual(loc.line, 88)
        self.assertEqual(loc.function, "start_app")

    def test_extract_unix_path_traceback(self):
        raw = 'Traceback (most recent call last):\n  File "/var/www/api/handlers/auth.py", line 142, in authenticate_user\nKeyError: \'token\''
        loc = ErrorParser.extract_location(raw)
        self.assertIsNotNone(loc)
        self.assertEqual(loc.file, "/var/www/api/handlers/auth.py")
        self.assertEqual(loc.line, 142)
        self.assertEqual(loc.function, "authenticate_user")

    def test_extract_inline_string_execution(self):
        raw = 'Traceback (most recent call last):\n  File "<string>", line 1, in <module>\nZeroDivisionError: division by zero'
        loc = ErrorParser.extract_location(raw)
        self.assertIsNotNone(loc)
        self.assertEqual(loc.file, "<string>")
        self.assertEqual(loc.line, 1)

    def test_user_frame_preferred_over_stdlib_deep_trace(self):
        raw = (
            'Traceback (most recent call last):\n'
            '  File "C:\\Users\\Admin\\project\\app.py", line 12, in <module>\n'
            '    data = fetch_url("http://localhost:8080")\n'
            '  File "C:\\Python312\\Lib\\urllib\\request.py", line 215, in urlopen\n'
            '    return opener.open(url, data, timeout)\n'
            '  File "C:\\Python312\\Lib\\urllib\\request.py", line 519, in open\n'
            '    response = self._open(req, data)\n'
            'urllib.error.URLError: <urlopen error [Errno 10061] Unknown error>'
        )
        loc = ErrorParser.extract_location(raw)
        self.assertIsNotNone(loc)
        self.assertIn("app.py", loc.file)
        self.assertEqual(loc.line, 12)

    # =========================================================================
    # 3. Fallback Safety & Non-Zero Exit Code Guarantees
    # =========================================================================
    def test_unknown_custom_exception_fallback(self):
        raw = "CustomEnterpriseServicePanic: Service gateway dropped RPC connection\nFile \"gateway.py\", line 55, in route_request"
        res = self.engine.diagnose(raw, command="python gateway.py", exit_code=1)
        self.assertFalse(res.is_known)
        self.assertEqual(res.rule_id, "unknown")
        self.assertIn("CustomEnterpriseServicePanic", res.original_error)
        self.assertIn("CustomEnterpriseServicePanic", res.explanation)
        self.assertIn("line 55", res.explanation)
        self.assertTrue(any("line 55" in s for s in res.suggestions))

    def test_silent_failure_no_output(self):
        res = self.engine.diagnose("", command="make build", exit_code=2)
        self.assertFalse(res.is_known)
        self.assertEqual(res.rule_id, "no-output")
        self.assertIn("without output", res.title.lower())
        self.assertTrue(any("verbose" in s.lower() for s in res.suggestions))

    def test_exit_code_non_zero_never_matches_when_rule_disallows_zero(self):
        """Rules must return None on exit_code == 0."""
        for rule in self.engine.registry.all_rules():
            # Standard error text with exit_code == 0
            match = rule.match(
                cleaned_output="Error: connection refused on port 8080",
                command="curl http://localhost:8080",
                exit_code=0
            )
            # Only HttpErrorRule matches exit_code 0 when explicit 4xx/5xx headers exist
            if rule.rule_id != "http-error":
                self.assertIsNone(match, f"Rule {rule.rule_id} incorrectly matched on exit code 0!")

    # =========================================================================
    # 4. Multiline Traceback & Dynamic Attribute Extraction
    # =========================================================================
    def test_multiline_python_traceback_with_comments(self):
        raw = (
            'Traceback (most recent call last):\n'
            '  File "calculator.py", line 20, in divide_all\n'
            '    res = [10 / x for x in [2, 1, 0]]\n'
            '          ^^^^^^\n'
            'ZeroDivisionError: division by zero'
        )
        res = self.engine.diagnose(raw, command="python calculator.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "zero-division-error")
        self.assertEqual(res.location.line, 20)
        self.assertEqual(res.location.function, "divide_all")

    def test_attribute_error_did_you_mean_suggestion_extracted(self):
        raw = "AttributeError: 'dict' object has no attribute 'valus'. Did you mean: 'values'?"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "runtime-attribute-error")
        self.assertTrue(any("values" in s and "valus" in s for s in res.suggestions))

if __name__ == "__main__":
    unittest.main()
