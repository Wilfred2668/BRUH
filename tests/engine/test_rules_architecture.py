"""Comprehensive validation tests for Phase 5.5 Rule Architecture Reorganization."""

import unittest
from bruh.engine.matcher import DiagnosticEngine
from bruh.engine.registry import RuleRegistry, get_default_registry, BUILTIN_RULES
from bruh.rules.base import BaseDiagnosticRule

# Verify direct imports from new package structure
from bruh.rules.languages.python.runtime.type_error import TypeErrorRule
from bruh.rules.languages.python.runtime.value_error import ValueErrorRule
from bruh.rules.languages.python.runtime.key_error import KeyErrorRule
from bruh.rules.languages.python.runtime.index_error import IndexErrorRule
from bruh.rules.languages.python.runtime.name_error import NameErrorRule
from bruh.rules.languages.python.runtime.runtime_attribute_error import RuntimeAttributeErrorRule
from bruh.rules.languages.python.runtime.zero_division_error import ZeroDivisionErrorRule
from bruh.rules.languages.python.runtime.recursion_error import RecursionErrorRule
from bruh.rules.languages.python.syntax.syntax_error import SyntaxErrorRule
from bruh.rules.languages.python.imports.module_not_found import ModuleNotFoundRule
from bruh.rules.languages.python.imports.import_error import ImportErrorRule
from bruh.rules.languages.python.data.json_decode_error import JSONDecodeErrorRule
from bruh.rules.languages.python.subprocess.subprocess_error import SubprocessErrorRule

from bruh.rules.domains.database.database_error import DatabaseErrorRule
from bruh.rules.domains.http.http_error import HttpErrorRule
from bruh.rules.domains.http.http_client_error import HttpClientErrorRule
from bruh.rules.domains.networking.connection_refused import ConnectionRefusedRule
from bruh.rules.domains.networking.port_in_use import PortInUseRule
from bruh.rules.domains.packages.package_not_found import PackageNotFoundRule
from bruh.rules.domains.packages.dependency_conflict import DependencyConflictRule
from bruh.rules.domains.git.git_errors import GitErrorRule

from bruh.rules.system.shell.command_not_found import CommandNotFoundRule
from bruh.rules.system.filesystem.file_not_found import FileNotFoundRule
from bruh.rules.system.filesystem.directory_not_found import DirectoryNotFoundRule
from bruh.rules.system.permissions.permission_denied import PermissionDeniedRule

ALL_EXPECTED_RULE_CLASSES = [
    PackageNotFoundRule,
    ModuleNotFoundRule,
    ImportErrorRule,
    PortInUseRule,
    CommandNotFoundRule,
    DatabaseErrorRule,
    JSONDecodeErrorRule,
    SubprocessErrorRule,
    RecursionErrorRule,
    ZeroDivisionErrorRule,
    KeyErrorRule,
    IndexErrorRule,
    NameErrorRule,
    HttpClientErrorRule,
    HttpErrorRule,
    TypeErrorRule,
    ValueErrorRule,
    RuntimeAttributeErrorRule,
    ConnectionRefusedRule,
    PermissionDeniedRule,
    DirectoryNotFoundRule,
    FileNotFoundRule,
    DependencyConflictRule,
    SyntaxErrorRule,
    GitErrorRule,
]

class TestRuleArchitecture(unittest.TestCase):

    def setUp(self):
        self.engine = DiagnosticEngine(registry=get_default_registry())

    # =========================================================================
    # 1. Structural & Registration Invariants
    # =========================================================================
    def test_all_25_rules_registered(self):
        """Verify all baseline and expansion rules are registered in the default registry."""
        rules = self.engine.registry.all_rules()
        self.assertGreaterEqual(len(rules), 25)
        self.assertGreaterEqual(len(BUILTIN_RULES), 25)

    def test_no_duplicate_rule_ids(self):
        """Verify no duplicate rule_id exists across all registered rules."""
        rules = self.engine.registry.all_rules()
        rule_ids = [r.rule_id for r in rules]
        self.assertEqual(len(rule_ids), len(set(rule_ids)))

    def test_every_rule_inherits_base_diagnostic_rule(self):
        """Verify every registered rule is an instance of BaseDiagnosticRule."""
        for rule_cls in ALL_EXPECTED_RULE_CLASSES:
            instance = rule_cls()
            self.assertIsInstance(instance, BaseDiagnosticRule)
            self.assertTrue(bool(instance.rule_id))
            self.assertTrue(bool(instance.name))
            self.assertTrue(bool(instance.category))
            self.assertIsInstance(instance.priority, int)

    def test_priority_ordering_is_strictly_descending(self):
        """Verify registry sorts all rules in strict descending priority order."""
        rules = self.engine.registry.all_rules()
        priorities = [r.priority for r in rules]
        self.assertEqual(priorities, sorted(priorities, reverse=True))

    # =========================================================================
    # 2. Reorganized Language / Domain / System Rule Tests
    # =========================================================================
    def test_python_runtime_rules(self):
        """Verify python runtime rules function after moving into languages/python/runtime/."""
        res_type = self.engine.diagnose("TypeError: 'int' object is not callable", command="python t.py", exit_code=1)
        self.assertTrue(res_type.is_known)
        self.assertEqual(res_type.rule_id, "type-error")

        res_val = self.engine.diagnose("ValueError: invalid literal for int() with base 10: 'abc'", command="python v.py", exit_code=1)
        self.assertEqual(res_val.rule_id, "value-error")

        res_key = self.engine.diagnose("KeyError: 'session_id'", command="python k.py", exit_code=1)
        self.assertEqual(res_key.rule_id, "key-error")

        res_idx = self.engine.diagnose("IndexError: list index out of range", command="python i.py", exit_code=1)
        self.assertEqual(res_idx.rule_id, "index-error")

        res_div = self.engine.diagnose("ZeroDivisionError: division by zero", command="python z.py", exit_code=1)
        self.assertEqual(res_div.rule_id, "zero-division-error")

    def test_python_imports_and_syntax_rules(self):
        """Verify import and syntax rules in languages/python/imports and languages/python/syntax."""
        res_mod = self.engine.diagnose("ModuleNotFoundError: No module named 'scipy'", command="python app.py", exit_code=1)
        self.assertEqual(res_mod.rule_id, "module-not-found")

        res_imp = self.engine.diagnose("ImportError: cannot import name 'fast_calc' from 'math'", command="python app.py", exit_code=1)
        self.assertEqual(res_imp.rule_id, "import-error")

        res_syn = self.engine.diagnose("SyntaxError: invalid syntax\nFile \"test.py\", line 4\n    for i in", command="python test.py", exit_code=1)
        self.assertEqual(res_syn.rule_id, "syntax-error")

    def test_domain_rules(self):
        """Verify domain rules in domains/ (database, http, networking, packages, git)."""
        res_db = self.engine.diagnose("psycopg2.OperationalError: password authentication failed for user 'app'", command="python db.py", exit_code=1)
        self.assertEqual(res_db.rule_id, "database-error")

        res_http = self.engine.diagnose("HTTP/1.1 502 Bad Gateway\nContent-Type: text/html", command="curl -i http://api.local", exit_code=0)
        self.assertEqual(res_http.rule_id, "http-error")

        res_port = self.engine.diagnose("Error: listen EADDRINUSE: address already in use :::8000", command="node app.js", exit_code=1)
        self.assertEqual(res_port.rule_id, "port-already-in-use")

        res_pkg = self.engine.diagnose("ERROR: No matching distribution found for package_12345", command="pip install package_12345", exit_code=1)
        self.assertEqual(res_pkg.rule_id, "package-not-found")

        res_git = self.engine.diagnose("fatal: not a git repository (or any of the parent directories): .git", command="git status", exit_code=128)
        self.assertEqual(res_git.rule_id, "git-error")

    def test_system_rules(self):
        """Verify system rules in system/ (shell, filesystem, permissions)."""
        res_cmd = self.engine.diagnose("bash: foobar123: command not found", command="foobar123", exit_code=127)
        self.assertEqual(res_cmd.rule_id, "command-not-found")

        res_file = self.engine.diagnose("FileNotFoundError: [Errno 2] No such file or directory: 'missing.json'", command="python run.py", exit_code=1)
        self.assertEqual(res_file.rule_id, "file-not-found")

        res_dir = self.engine.diagnose("Set-Location : Cannot find path 'D:\\nonexistent_dir'", command="cd D:\\nonexistent_dir", exit_code=1)
        self.assertEqual(res_dir.rule_id, "directory-not-found")

        res_perm = self.engine.diagnose("PermissionError: [Errno 13] Permission denied: '/etc/shadow'", command="python write.py", exit_code=1)
        self.assertEqual(res_perm.rule_id, "permission-denied")

if __name__ == "__main__":
    unittest.main()
