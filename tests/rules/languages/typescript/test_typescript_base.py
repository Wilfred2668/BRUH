"""Unit and regression tests for Phase 8 TypeScript compiler diagnostics."""

import unittest
from bruh.engine.matcher import DiagnosticEngine
from bruh.engine.parser import ErrorParser
from bruh.engine.registry import get_default_registry, BUILTIN_RULES
from bruh.rules.languages.typescript.types.ts_type_mismatch import TSTypeMismatchRule
from bruh.rules.languages.typescript.types.ts_property_not_found import TSPropertyNotFoundRule
from bruh.rules.languages.typescript.compiler.ts_cannot_find_name import TSCannotFindNameRule
from bruh.rules.languages.typescript.compiler.ts_argument_count import TSArgumentCountRule
from bruh.rules.languages.typescript.types.ts_implicit_any import TSImplicitAnyRule
from bruh.rules.languages.typescript.modules.ts_module_not_found import TSModuleNotFoundRule
from bruh.rules.languages.typescript.syntax.ts_syntax_error import TSSyntaxErrorRule

class TestTypeScriptBaseDiagnostics(unittest.TestCase):

    def setUp(self):
        self.engine = DiagnosticEngine(registry=get_default_registry())

    # =========================================================================
    # 1. Type Mismatch Tests (TS2322, TS2345)
    # =========================================================================
    def test_ts2322_variable_type_mismatch(self):
        raw = "test.ts(1,5): error TS2322: Type 'string' is not assignable to type 'number'."
        res = self.engine.diagnose(raw, command="tsc --noEmit test.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-type-mismatch")
        self.assertIn("Type Mismatch", res.title)
        self.assertIn("number", res.explanation)
        self.assertIn("string", res.explanation)
        self.assertTrue(any("Change the assigned value" in s for s in res.suggestions))

    def test_ts2345_argument_type_mismatch(self):
        raw = "test.ts(2,7): error TS2345: Argument of type 'number' is not assignable to parameter of type 'string'."
        res = self.engine.diagnose(raw, command="tsc --noEmit test.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-type-mismatch")
        self.assertIn("parameter 'string'", res.title)
        self.assertIn("incompatible type 'number'", res.explanation)

    # =========================================================================
    # 2. Property Does Not Exist Tests (TS2339)
    # =========================================================================
    def test_ts2339_property_does_not_exist(self):
        raw = "test.ts(6,18): error TS2339: Property 'age' does not exist on type 'User'."
        res = self.engine.diagnose(raw, command="tsc --noEmit test.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-property-not-found")
        self.assertIn("Property 'age' does not exist on type 'User'", res.title)
        self.assertIn("User", res.explanation)
        self.assertTrue(any("User" in s and "age" in s for s in res.suggestions))

    def test_ts2339_property_with_suggestion(self):
        raw = "test.ts(3,10): error TS2339: Property 'lenght' does not exist on type 'string[]'. Did you mean 'length'?"
        res = self.engine.diagnose(raw, command="tsc --noEmit test.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-property-not-found")
        self.assertTrue(any("Did you mean 'length'?" in s for s in res.suggestions))

    # =========================================================================
    # 3. Cannot Find Name Tests (TS2304, TS2552)
    # =========================================================================
    def test_ts2304_cannot_find_name(self):
        raw = "test.ts(1,13): error TS2304: Cannot find name 'undefinedVariable'."
        res = self.engine.diagnose(raw, command="tsc --noEmit test.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-cannot-find-name")
        self.assertIn("Cannot find name 'undefinedVariable' (TS2304)", res.title)
        self.assertIn("undefinedVariable", res.explanation)
        self.assertTrue(any("undefinedVariable" in s for s in res.suggestions))

    def test_ts2552_cannot_find_name_with_suggestion(self):
        raw = "test.ts(2,5): error TS2552: Cannot find name 'usr'. Did you mean 'user'?"
        res = self.engine.diagnose(raw, command="tsc --noEmit test.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-cannot-find-name")
        self.assertIn("Cannot find name 'usr' (TS2552)", res.title)
        self.assertTrue(any("Did you mean 'user'?" in s for s in res.suggestions))

    # =========================================================================
    # 4. Missing Module & Declarations Tests (TS2307)
    # =========================================================================
    def test_ts2307_missing_npm_package_declarations(self):
        raw = "test.ts(1,23): error TS2307: Cannot find module 'definitely-missing-package' or its corresponding type declarations."
        res = self.engine.diagnose(raw, command="tsc --noEmit test.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-module-not-found")
        self.assertIn("definitely-missing-package", res.title)
        self.assertTrue(any("npm install definitely-missing-package" in s for s in res.suggestions))
        self.assertTrue(any("@types/definitely-missing-package" in s for s in res.suggestions))

    def test_ts2307_missing_local_file(self):
        raw = "test.ts(1,20): error TS2307: Cannot find module './utils/helper' or its corresponding type declarations."
        res = self.engine.diagnose(raw, command="tsc --noEmit test.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-module-not-found")
        self.assertIn("Cannot find local module './utils/helper'", res.title)
        self.assertTrue(any("relative file path" in s for s in res.suggestions))

    # =========================================================================
    # 5. Argument Count Tests (TS2554)
    # =========================================================================
    def test_ts2554_wrong_argument_count(self):
        raw = "test.ts(2,1): error TS2554: Expected 2 arguments, but got 1."
        res = self.engine.diagnose(raw, command="tsc --noEmit test.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-argument-count")
        self.assertIn("Expected 2 argument(s), but got 1", res.title)
        self.assertIn("expects 2 argument(s)", res.explanation)
        self.assertTrue(any("supply all 2" in s for s in res.suggestions))

    # =========================================================================
    # 6. Implicit Any Tests (TS7006)
    # =========================================================================
    def test_ts7006_implicit_any_parameter(self):
        raw = "test.ts(1,16): error TS7006: Parameter 'name' implicitly has an 'any' type."
        res = self.engine.diagnose(raw, command="tsc --noEmit --noImplicitAny test.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-implicit-any")
        self.assertIn("Parameter 'name' implicitly has an 'any' type", res.title)
        self.assertIn("noImplicitAny", res.explanation)
        self.assertTrue(any("name: string" in s for s in res.suggestions))

    # =========================================================================
    # 7. Syntax & Parser Error Tests (TS1000-series)
    # =========================================================================
    def test_ts1109_expression_expected(self):
        raw = "test.ts(1,19): error TS1109: Expression expected."
        res = self.engine.diagnose(raw, command="tsc --noEmit test.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-syntax-error")
        self.assertIn("Expression expected", res.title)
        self.assertIn("TS1109", res.title)

    def test_ts1005_semicolon_expected(self):
        raw = "test.ts(2,5): error TS1005: ';' expected."
        res = self.engine.diagnose(raw, command="tsc --noEmit test.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-syntax-error")
        self.assertIn("';' expected", res.title)

    # =========================================================================
    # 8. Location Extraction Tests (Windows, POSIX, Colon format)
    # =========================================================================
    def test_extract_ts_windows_path_location(self):
        raw = "D:\\Codes\\Project\\src\\app.ts(14,22): error TS2322: Type 'boolean' is not assignable to type 'string'."
        loc = ErrorParser.extract_location(raw)
        self.assertIsNotNone(loc)
        self.assertIn("app.ts", loc.file)
        self.assertEqual(loc.line, 14)
        self.assertEqual(loc.column, 22)

    def test_extract_ts_posix_path_location(self):
        raw = "/var/www/frontend/src/components/Header.tsx(45,8): error TS2339: Property 'title' does not exist on type 'Props'."
        loc = ErrorParser.extract_location(raw)
        self.assertIsNotNone(loc)
        self.assertEqual(loc.file, "/var/www/frontend/src/components/Header.tsx")
        self.assertEqual(loc.line, 45)
        self.assertEqual(loc.column, 8)

    def test_extract_ts_colon_format_location(self):
        raw = "src/index.ts:10:5 - error TS2304: Cannot find name 'Config'."
        loc = ErrorParser.extract_location(raw)
        self.assertIsNotNone(loc)
        self.assertIn("index.ts", loc.file)
        self.assertEqual(loc.line, 10)
        self.assertEqual(loc.column, 5)

    # =========================================================================
    # 9. Priority & Non-Interference Invariants
    # =========================================================================
    def test_generic_js_syntax_error_not_stolen_by_typescript(self):
        raw = (
            "[eval]:1\n"
            "function test() {\n"
            "               ^\n"
            "SyntaxError: Unexpected token '{'"
        )
        res = self.engine.diagnose(raw, command="node script.js", exit_code=1)
        self.assertEqual(res.rule_id, "js-syntax-error")

    def test_python_type_error_not_stolen_by_typescript(self):
        raw = "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertEqual(res.rule_id, "type-error")

    def test_all_38_rules_registered_and_unique(self):
        rules = self.engine.registry.all_rules()
        self.assertGreaterEqual(len(rules), 38)
        self.assertGreaterEqual(len(BUILTIN_RULES), 38)

        rule_ids = [r.rule_id for r in rules]
        self.assertEqual(len(rule_ids), len(set(rule_ids)))

if __name__ == "__main__":
    unittest.main()
