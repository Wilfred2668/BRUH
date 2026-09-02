"""Unit tests for Phase 11 BRUH Standalone Tool & CLI behavior."""

import unittest
from unittest.mock import patch
import sys
import io
from bruh.cli import main, create_parser

class TestBruhCliTool(unittest.TestCase):

    def test_cli_parser_creation(self):
        parser = create_parser()
        self.assertIsNotNone(parser)
        self.assertEqual(parser.prog, "bruh")

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_explain_command(self, mock_stdout):
        with patch.object(sys, "argv", ["bruh", "explain", "ZeroDivisionError: division by zero"]):
            exit_code = main()
            self.assertEqual(exit_code, 0)
            output = mock_stdout.getvalue()
            self.assertIn("Division by zero", output)
            self.assertIn("Bruh, what happened?", output)
            self.assertIn("Try this", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_check_status_command(self, mock_stdout):
        with patch.object(sys, "argv", ["bruh", "check"]):
            exit_code = main()
            self.assertEqual(exit_code, 0)
            output = mock_stdout.getvalue()
            self.assertIn("Bruh Diagnostic Status", output)
            self.assertIn("Active Rules:", output)
            self.assertIn("48 active diagnostic rules", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_direct_command_execution_failure(self, mock_stdout):
        # Run python -c "1/0" directly through bruh
        with patch.object(sys, "argv", ["bruh", "python", "-c", "1/0"]):
            exit_code = main()
            self.assertEqual(exit_code, 0)
            output = mock_stdout.getvalue()
            self.assertIn("Division by zero", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_direct_command_execution_success(self, mock_stdout):
        # Run python -c "print('ok')" directly through bruh
        with patch.object(sys, "argv", ["bruh", "python", "-c", "print('ok')"]):
            exit_code = main()
            self.assertEqual(exit_code, 0)
            output = mock_stdout.getvalue()
            self.assertIn("You're good", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_direct_ts_command_execution(self, mock_stdout):
        # Pass a TS compiler error string directly to explain
        with patch.object(sys, "argv", ["bruh", "explain", "test.ts(1,5): error TS2322: Type 'string' is not assignable to type 'number'."]):
            exit_code = main()
            self.assertEqual(exit_code, 0)
            output = mock_stdout.getvalue()
            self.assertIn("Type Mismatch", output)
            self.assertIn("TS2322", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_unknown_error_safety(self, mock_stdout):
        # Unknown error does not crash
        with patch.object(sys, "argv", ["bruh", "explain", "CustomFatalFrameworkError: something exploded in subsystem 42"]):
            exit_code = main()
            self.assertEqual(exit_code, 0)
            output = mock_stdout.getvalue()
            self.assertIn("BRUH", output)

if __name__ == "__main__":
    unittest.main()
