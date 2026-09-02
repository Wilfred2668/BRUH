"""Unit tests for cross-cutting diagnostic rules and dynamic variable extractions."""

import unittest
from bruh.rules.languages.python.imports.module_not_found import ModuleNotFoundRule
from bruh.rules.languages.javascript.imports.js_module_not_found import JSModuleNotFoundRule
from bruh.rules.domains.networking.port_in_use import PortInUseRule
from bruh.rules.domains.networking.connection_refused import ConnectionRefusedRule
from bruh.rules.domains.packages.dependency_conflict import DependencyConflictRule
from bruh.rules.languages.python.syntax.syntax_error import SyntaxErrorRule
from bruh.rules.domains.git.git_errors import GitErrorRule
from tests.fixtures import sample_errors

class TestDiagnosticRules(unittest.TestCase):

    def test_module_not_found_python(self):
        rule = ModuleNotFoundRule()
        match = rule.match(sample_errors.PYTHON_MODULE_NOT_FOUND_PANDAS)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertEqual(match.extracted_vars["module"], "pandas")
        self.assertEqual(match.extracted_vars["ecosystem"], "python")

        explanation = rule.generate_explanation(match.extracted_vars)
        self.assertIn("pandas", explanation)
        self.assertIn("Python tried to import", explanation)

        suggestions = rule.generate_suggestions(match.extracted_vars)
        self.assertTrue(any("pip install pandas" in s for s in suggestions))

    def test_module_not_found_node(self):
        rule = JSModuleNotFoundRule()
        match = rule.match(sample_errors.NODE_MODULE_NOT_FOUND_EXPRESS)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertEqual(match.extracted_vars["module"], "express")

        suggestions = rule.generate_suggestions(match.extracted_vars)
        self.assertTrue(any("npm install" in s for s in suggestions))
        self.assertTrue(any("package.json" in s for s in suggestions))

    def test_port_in_use_node(self):
        rule = PortInUseRule()
        match = rule.match(sample_errors.NODE_PORT_IN_USE)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertEqual(match.extracted_vars["port"], "3000")

        explanation = rule.generate_explanation(match.extracted_vars)
        self.assertIn("3000", explanation)

        suggestions = rule.generate_suggestions(match.extracted_vars)
        self.assertTrue(any("3000" in s for s in suggestions))

    def test_port_in_use_python(self):
        rule = PortInUseRule()
        match = rule.match(sample_errors.PYTHON_PORT_IN_USE)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)

    def test_connection_refused_postgres(self):
        rule = ConnectionRefusedRule()
        match = rule.match(sample_errors.CONNECTION_REFUSED_POSTGRES)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertEqual(match.extracted_vars["port"], "5432")
        self.assertEqual(match.extracted_vars["service"], "PostgreSQL")

    def test_connection_refused_python(self):
        rule = ConnectionRefusedRule()
        match = rule.match(sample_errors.CONNECTION_REFUSED_PYTHON)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)

    def test_dependency_conflict_npm(self):
        rule = DependencyConflictRule()
        match = rule.match(sample_errors.NPM_DEPENDENCY_CONFLICT)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertEqual(match.extracted_vars["ecosystem"], "npm")
        suggestions = rule.generate_suggestions(match.extracted_vars)
        self.assertTrue(any("--legacy-peer-deps" in s for s in suggestions))

    def test_syntax_error_python(self):
        rule = SyntaxErrorRule()
        match = rule.match(sample_errors.PYTHON_SYNTAX_ERROR)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertFalse(match.extracted_vars["is_indent"])

    def test_indentation_error_python(self):
        rule = SyntaxErrorRule()
        match = rule.match(sample_errors.PYTHON_INDENTATION_ERROR)
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertTrue(match.extracted_vars["is_indent"])

    def test_git_not_a_repo(self):
        rule = GitErrorRule()
        match = rule.match(sample_errors.GIT_NOT_A_REPO, command="git status")
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertEqual(match.extracted_vars["issue"], "not_repo")

    def test_git_refusing_unrelated(self):
        rule = GitErrorRule()
        match = rule.match(sample_errors.GIT_REFUSING_UNRELATED, command="git pull origin main")
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertEqual(match.extracted_vars["issue"], "unrelated_histories")

    def test_git_push_rejected(self):
        rule = GitErrorRule()
        match = rule.match(sample_errors.GIT_PUSH_REJECTED, command="git push")
        self.assertIsNotNone(match)
        self.assertTrue(match.matched)
        self.assertEqual(match.extracted_vars["issue"], "push_rejected")

if __name__ == "__main__":
    unittest.main()
