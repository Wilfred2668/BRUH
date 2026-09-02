"""Comprehensive regression and contract tests for Phase 1 final UX and reliability polish."""

import unittest
import os
import io
import time
import tempfile
from pathlib import Path
from unittest.mock import patch

from bruh.engine.matcher import DiagnosticEngine
from bruh.engine.registry import get_default_registry
from bruh.presentation.renderer import TerminalRenderer
from bruh.presentation.ansi import strip_ansi
from bruh.capture.context import CommandContext
from bruh.capture.session import SessionStore
from bruh.capture.history import is_multiline_fragment, reconstruct_multiline
from bruh.cli import main

class TestEndToEndRegression(unittest.TestCase):

    def setUp(self):
        self.engine = DiagnosticEngine(registry=get_default_registry())

    def test_1_successful_git_not_diagnosed_as_error(self):
        """Test 1: Successful Git push (Everything up-to-date) must NOT match git-error and must report success."""
        git_output = "Everything up-to-date"
        result = self.engine.diagnose(git_output, command="git push origin main", exit_code=0)
        # Rule matcher should NOT match GitErrorRule when exit_code == 0
        rule = get_default_registry().get_rule("git-error")
        match = rule.match(git_output, command="git push origin main", exit_code=0)
        self.assertIsNone(match)

        # CLI should render success screen
        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "last_session.json"
            store = SessionStore(session_file=session_file)
            store.save(CommandContext(
                command="git push origin main",
                exit_code=0,
                output="Everything up-to-date",
                timestamp=time.time()
            ))
            with patch("bruh.cli.LAST_SESSION_FILE", session_file):
                with patch("bruh.cli.get_last_command_from_history", return_value=(None, 0)):
                    with patch("sys.stdout", new=io.StringIO()) as fake_out:
                        with patch("sys.argv", ["bruh"]):
                            code = main()
                            self.assertEqual(code, 0)
                            out = strip_ansi(fake_out.getvalue())
                            self.assertIn("You're good", out)
                            self.assertIn("git push origin main", out)

    def test_2_powershell_directory_missing(self):
        """Test 2: cd abc with Cannot find path must diagnose as directory-not-found."""
        ps_output = "Set-Location : Cannot find path 'D:\\Codes\\BRUH\\abc' because it does not exist."
        result = self.engine.diagnose(ps_output, command="cd abc", exit_code=1)
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "directory-not-found")
        self.assertIn("Directory not found", result.title)
        self.assertIn("directory that doesn't exist", result.explanation)
        self.assertTrue(any("folder name for a typo" in s for s in result.suggestions))

    def test_3_python_file_missing(self):
        """Test 3: python app.py with can't open file must diagnose as file-not-found."""
        py_output = "can't open file 'D:\\Codes\\BRUH\\app.py': [Errno 2] No such file or directory"
        result = self.engine.diagnose(py_output, command="python app.py", exit_code=1)
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "file-not-found")
        self.assertIn("File not found", result.title)
        self.assertIn("Python tried to open app.py", result.explanation)
        self.assertTrue(any("Check that app.py exists" in s for s in result.suggestions))

    def test_4_pip_package_missing(self):
        """Test 4: pip install djskcnd with No matching distribution must diagnose as package-not-found."""
        pip_output = (
            "ERROR: Could not find a version that satisfies the requirement djskcnd (from versions: none)\n"
            "ERROR: No matching distribution found for djskcnd"
        )
        result = self.engine.diagnose(pip_output, command="pip install djskcnd", exit_code=1)
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "package-not-found")
        self.assertIn("Package not found", result.title)
        self.assertIn("djskcnd", result.explanation)
        self.assertTrue(any("package name for a typo" in s for s in result.suggestions))
        # Ensure no network URL is generated
        self.assertFalse(any("http://" in s or "https://" in s for s in result.suggestions))

    def test_5_python_module_missing(self):
        """Test 5: ModuleNotFoundError with definitely_missing_package must diagnose as module-not-found."""
        py_mod_output = "ModuleNotFoundError: No module named 'definitely_missing_package'"
        result = self.engine.diagnose(py_mod_output, command="python script.py", exit_code=1)
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "module-not-found")
        self.assertIn("Module not found", result.title)
        self.assertIn("definitely_missing_package", result.explanation)
        self.assertTrue(any("pip install definitely_missing_package" in s for s in result.suggestions))

    def test_6_pip_duplicate_versions(self):
        """Test 6: pip install requests==2.28.0 requests==2.32.0 must explicitly identify both versions."""
        pip_conflict_output = (
            "Cannot install requests==2.28.0 and requests==2.32.0 because these package versions have conflicting dependencies."
        )
        result = self.engine.diagnose(pip_conflict_output, command="pip install requests==2.28.0 requests==2.32.0", exit_code=1)
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "dependency-conflict")
        self.assertIn("requests", result.explanation)
        self.assertIn("2.28.0", result.explanation)
        self.assertIn("2.32.0", result.explanation)
        self.assertTrue(any("Pick the version you actually want" in s for s in result.suggestions))

    def test_7_node_module_missing(self):
        """Test 7: Error: Cannot find module 'this-package-does-not-exist' must diagnose as module-not-found."""
        node_mod_output = "Error: Cannot find module 'this-package-does-not-exist'\nRequire stack:\n- index.js"
        result = self.engine.diagnose(node_mod_output, command="node index.js", exit_code=1)
        self.assertTrue(result.is_known)
        self.assertIn(result.rule_id, ("module-not-found", "js-module-not-found"))
        self.assertIn("this-package-does-not-exist", result.explanation)
        self.assertTrue(any("module name for a typo" in s for s in result.suggestions))
        self.assertTrue(any("npm install" in s for s in result.suggestions))

    def test_8_node_port_conflict(self):
        """Test 8: Error: listen EADDRINUSE :::3000 must dynamically use port 3000 and simple suggestions."""
        port_output = "Error: listen EADDRINUSE: address already in use :::3000"
        result = self.engine.diagnose(port_output, command="npm start", exit_code=1)
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "port-already-in-use")
        self.assertIn("3000", result.explanation)
        suggestions = result.suggestions
        self.assertIn("3000", suggestions[0])
        self.assertIn("Close the other server", suggestions[0])

    def test_9_unknown_runtime_error(self):
        """Test 9: RuntimeError: BRUH_UNKNOWN_TEST_12345 must report unknown without inventing diagnosis."""
        unknown_output = (
            "Traceback (most recent call last):\n"
            "  File \"test_unknown.py\", line 11, in process_payment\n"
            "    raise RuntimeError(\"BRUH_UNKNOWN_TEST_12345\")\n"
            "RuntimeError: BRUH_UNKNOWN_TEST_12345"
        )
        result = self.engine.diagnose(unknown_output, command="python test_unknown.py", exit_code=1)
        self.assertFalse(result.is_known)
        self.assertEqual(result.rule_id, "unknown")
        self.assertIn("RuntimeError", result.explanation)
        self.assertIn("line 11", result.explanation)
        self.assertTrue(any("line 11" in s for s in result.suggestions))

    def test_10_multiline_powershell_safety(self):
        """Test 10: Multiline here-string fragments must be detected and not run as false commands."""
        fragment = '"@ | Set-Content test_unknown.py'
        self.assertTrue(is_multiline_fragment(fragment))

        lines = [
            '@"',
            'def level1():',
            '    level2()',
            '"@ | Set-Content test_unknown.py'
        ]
        reconstructed = reconstruct_multiline(lines, 3)
        self.assertTrue(reconstructed.startswith('@"'))
        self.assertTrue(reconstructed.endswith('Set-Content test_unknown.py'))

    def test_11_output_visual_contract(self):
        """Test 11: Verify every diagnostic output contains the exact core sections."""
        # 1. Known Diagnostic
        port_res = self.engine.diagnose("Error: listen EADDRINUSE: address already in use :::3000", command="node app.js")
        port_text = strip_ansi(TerminalRenderer.render(port_res))
        self.assertIn("BRUH", port_text)
        self.assertIn("💀 Port 3000 already in use", port_text)
        self.assertIn("Bruh, what happened?", port_text)
        self.assertIn("Try this", port_text)
        self.assertNotIn("In normal human language", port_text)
        self.assertNotIn("What I can tell", port_text)

        # 2. Unknown Diagnostic
        unk_res = self.engine.diagnose("RuntimeError: BRUH_UNKNOWN_TEST_12345\nFile \"test.py\", line 5", command="python test.py")
        unk_text = strip_ansi(TerminalRenderer.render(unk_res))
        self.assertIn("BRUH", unk_text)
        self.assertIn("I don't recognize this error yet", unk_text)
        self.assertIn("Where", unk_text)
        self.assertIn("test.py:5", unk_text)
        self.assertIn("Bruh, what happened?", unk_text)
        self.assertIn("Try this", unk_text)
        self.assertNotIn("In normal human language", unk_text)
        self.assertNotIn("What I can tell", unk_text)

if __name__ == "__main__":
    unittest.main()
