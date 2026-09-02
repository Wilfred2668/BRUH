"""Unit tests for System rules (Command Not Found, Permission Denied, File Not Found)."""

import unittest
from bruh.rules.system.shell.command_not_found import CommandNotFoundRule
from bruh.rules.system.permissions.permission_denied import PermissionDeniedRule
from bruh.rules.system.filesystem.file_not_found import FileNotFoundRule
from tests.fixtures import sample_errors

class TestSystemRules(unittest.TestCase):

    def test_command_not_found_powershell(self):
        rule = CommandNotFoundRule()
        match = rule.match(sample_errors.COMMAND_NOT_FOUND_POWERSHELL)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertEqual(match.extracted_vars["command"], "pnpm")

    def test_command_not_found_bash(self):
        rule = CommandNotFoundRule()
        match = rule.match(sample_errors.COMMAND_NOT_FOUND_BASH)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertEqual(match.extracted_vars["command"], "docker-compose")

    def test_command_not_found_cmd(self):
        rule = CommandNotFoundRule()
        match = rule.match(sample_errors.COMMAND_NOT_FOUND_WINDOWS_CMD)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertEqual(match.extracted_vars["command"], "mvn")

    def test_permission_denied_node(self):
        rule = PermissionDeniedRule()
        match = rule.match(sample_errors.PERMISSION_DENIED_NODE)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertIn("/usr/local/lib/node_modules", match.extracted_vars["path"])

    def test_permission_denied_python(self):
        rule = PermissionDeniedRule()
        match = rule.match(sample_errors.PERMISSION_DENIED_PYTHON)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertEqual(match.extracted_vars["path"], "/etc/config.json")

    def test_file_not_found_node(self):
        rule = FileNotFoundRule()
        match = rule.match(sample_errors.FILE_NOT_FOUND_NODE)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertEqual(match.extracted_vars["path"], "./config/settings.json")

    def test_file_not_found_python(self):
        rule = FileNotFoundRule()
        match = rule.match(sample_errors.FILE_NOT_FOUND_PYTHON)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertEqual(match.extracted_vars["path"], "dataset/train.csv")

if __name__ == "__main__":
    unittest.main()
