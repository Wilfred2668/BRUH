"""Unit tests for shell detector and shell integration modules."""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from bruh.shell.detector import ShellDetector
from bruh.shell.integration import ShellIntegration, HOOK_MARKER_START, HOOK_MARKER_END

class TestShellIntegration(unittest.TestCase):

    def test_get_init_script_powershell(self):
        script = ShellIntegration.get_init_script("powershell")
        self.assertIn("__bruh_prompt_hook", script)

    def test_get_init_script_bash(self):
        script = ShellIntegration.get_init_script("bash")
        self.assertIn("PROMPT_COMMAND", script)

    def test_get_init_script_zsh(self):
        script = ShellIntegration.get_init_script("zsh")
        self.assertIn("add-zsh-hook", script)

    def test_install_and_uninstall_profile_hook(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_profile = Path(tmpdir) / ".bashrc"
            fake_profile.write_text("# user config\nexport FOO=1\n", encoding="utf-8")

            with patch.object(ShellDetector, "detect_shell", return_value=("bash", fake_profile)):
                # 1. Install
                success, msg = ShellIntegration.install("bash")
                self.assertTrue(success)
                content = fake_profile.read_text(encoding="utf-8")
                self.assertIn(HOOK_MARKER_START, content)
                self.assertIn(HOOK_MARKER_END, content)

                # 2. Idempotency test (install again should not duplicate)
                success2, msg2 = ShellIntegration.install("bash")
                self.assertTrue(success2)
                self.assertEqual(content.count(HOOK_MARKER_START), 1)

                # 3. Uninstall
                uninst_ok, uninst_msg = ShellIntegration.uninstall("bash")
                self.assertTrue(uninst_ok)
                uninstalled_content = fake_profile.read_text(encoding="utf-8")
                self.assertNotIn(HOOK_MARKER_START, uninstalled_content)
                self.assertIn("export FOO=1", uninstalled_content)

if __name__ == "__main__":
    unittest.main()
