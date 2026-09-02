"""Packaging and distribution invariant tests for Phase 6."""

import unittest
import importlib
import importlib.util
from pathlib import Path
from bruh.cli import main
from bruh.engine.registry import get_default_registry, BUILTIN_RULES
from bruh.shell.integration import ShellIntegration

class TestPackagingAndDistribution(unittest.TestCase):

    def test_cli_entrypoint_callable(self):
        """Verify the console script entry point function bruh.cli:main is callable."""
        self.assertTrue(callable(main))

    def test_all_25_rules_importable_and_instantiable(self):
        """Verify every single built-in rule class in the distribution can be instantiated."""
        self.assertGreaterEqual(len(BUILTIN_RULES), 25)
        for rule_cls in BUILTIN_RULES:
            instance = rule_cls()
            self.assertTrue(bool(instance.rule_id))
            self.assertTrue(bool(instance.name))
            self.assertIsInstance(instance.priority, int)

    def test_shell_script_assets_present_in_package(self):
        """Verify shell integration assets (bruh.ps1, bruh.bash, bruh.zsh) are present in the package."""
        ps1_script = ShellIntegration.get_init_script("powershell")
        self.assertTrue(bool(ps1_script))
        self.assertIn("function global:bruh", ps1_script)

        bash_script = ShellIntegration.get_init_script("bash")
        self.assertTrue(bool(bash_script))
        self.assertIn("__bruh_precmd", bash_script)

        zsh_script = ShellIntegration.get_init_script("zsh")
        self.assertTrue(bool(zsh_script))
        self.assertIn("__bruh_precmd", zsh_script)

    def test_package_structure_submodules_importable(self):
        """Verify all submodules in the package namespace can be dynamically imported."""
        modules_to_test = [
            "bruh",
            "bruh.cli",
            "bruh.config",
            "bruh.capture.context",
            "bruh.capture.history",
            "bruh.capture.session",
            "bruh.engine.models",
            "bruh.engine.parser",
            "bruh.engine.extractors",
            "bruh.engine.matcher",
            "bruh.engine.registry",
            "bruh.presentation.ansi",
            "bruh.presentation.banner",
            "bruh.presentation.renderer",
            "bruh.shell.detector",
            "bruh.shell.integration",
            "bruh.rules.base",
            "bruh.rules.languages.python.runtime.type_error",
            "bruh.rules.languages.python.runtime.value_error",
            "bruh.rules.languages.python.runtime.key_error",
            "bruh.rules.languages.python.runtime.index_error",
            "bruh.rules.languages.python.runtime.name_error",
            "bruh.rules.languages.python.runtime.runtime_attribute_error",
            "bruh.rules.languages.python.runtime.zero_division_error",
            "bruh.rules.languages.python.runtime.recursion_error",
            "bruh.rules.languages.python.syntax.syntax_error",
            "bruh.rules.languages.python.imports.module_not_found",
            "bruh.rules.languages.python.imports.import_error",
            "bruh.rules.languages.python.data.json_decode_error",
            "bruh.rules.languages.python.subprocess.subprocess_error",
            "bruh.rules.domains.database.database_error",
            "bruh.rules.domains.http.http_error",
            "bruh.rules.domains.http.http_client_error",
            "bruh.rules.domains.networking.connection_refused",
            "bruh.rules.domains.networking.port_in_use",
            "bruh.rules.domains.packages.package_not_found",
            "bruh.rules.domains.packages.dependency_conflict",
            "bruh.rules.domains.git.git_errors",
            "bruh.rules.system.shell.command_not_found",
            "bruh.rules.system.filesystem.file_not_found",
            "bruh.rules.system.filesystem.directory_not_found",
            "bruh.rules.system.permissions.permission_denied",
        ]
        for mod_name in modules_to_test:
            mod = importlib.import_module(mod_name)
            self.assertIsNotNone(mod, f"Module {mod_name} failed to import!")

    def test_package_main_execution_hook(self):
        """Verify python -m bruh entry point is present."""
        spec = importlib.util.find_spec("bruh.__main__")
        self.assertIsNotNone(spec)

if __name__ == "__main__":
    unittest.main()
