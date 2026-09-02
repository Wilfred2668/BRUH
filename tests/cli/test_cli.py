"""Unit tests for the Bruh CLI interface."""

import io
import unittest
from unittest.mock import patch
from bruh.cli import main, create_parser
from bruh.capture.session import SessionStore
from bruh.capture.context import CommandContext
import tempfile
from pathlib import Path

class TestCLI(unittest.TestCase):

    def test_parser_version(self):
        parser = create_parser()
        with self.assertRaises(SystemExit) as cm:
            parser.parse_args(["--version"])
        self.assertEqual(cm.exception.code, 0)

    def test_explain_subcommand(self):
        err_msg = "ModuleNotFoundError: No module named 'scipy'"
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            with patch("sys.argv", ["bruh", "explain", err_msg]):
                code = main()
                self.assertEqual(code, 0)
                output = fake_out.getvalue()
                self.assertIn("scipy", output)
                self.assertIn("Bruh, what happened?", output)

    def test_check_subcommand(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            with patch("sys.argv", ["bruh", "check"]):
                code = main()
                self.assertEqual(code, 0)
                output = fake_out.getvalue()
                self.assertIn("Bruh Diagnostic Status", output)
                self.assertIn("module-not-found", output)
                self.assertIn("port-already-in-use", output)

    def test_init_subcommand(self):
        with patch("sys.stdout", new=io.StringIO()) as fake_out:
            with patch("sys.argv", ["bruh", "init", "bash"]):
                code = main()
                self.assertEqual(code, 0)
                output = fake_out.getvalue()
                self.assertIn("PROMPT_COMMAND", output)

    def test_record_subcommand(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "last_session.json"
            with patch("bruh.cli.LAST_SESSION_FILE", session_file):
                with patch("sys.argv", [
                    "bruh", "record",
                    "--command", "pytest",
                    "--exit-code", "2",
                    "--output", "AssertionError: Expected 5 == 4"
                ]):
                    code = main()
                    self.assertEqual(code, 0)
                    store = SessionStore(session_file=session_file)
                    loaded = store.load()
                    self.assertIsNotNone(loaded)
                    self.assertEqual(loaded.command, "pytest")
                    self.assertEqual(loaded.exit_code, 2)
                    self.assertIn("AssertionError", loaded.output)

if __name__ == "__main__":
    unittest.main()
