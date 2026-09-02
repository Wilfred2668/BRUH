"""Unit and regression tests for Phase 10 Expanded TypeScript Diagnostics."""

import unittest
from bruh.engine.matcher import DiagnosticEngine
from bruh.engine.parser import ErrorParser
from bruh.engine.registry import get_default_registry, BUILTIN_RULES
from bruh.rules.languages.typescript.types.ts_null_undefined import TSNullUndefinedRule
from bruh.rules.languages.typescript.types.ts_readonly_assignment import TSReadonlyAssignmentRule
from bruh.rules.languages.typescript.compiler.ts_missing_return import TSMissingReturnRule
from bruh.rules.languages.typescript.compiler.ts_class_inheritance import TSClassInheritanceRule
from bruh.rules.languages.typescript.types.ts_type_constraint import TSTypeConstraintRule
from bruh.rules.languages.typescript.syntax.ts_async_await import TSAsyncAwaitRule

class TestTypeScriptHighValueDiagnostics(unittest.TestCase):

    def setUp(self):
        self.engine = DiagnosticEngine(registry=get_default_registry())

    # =========================================================================
    # 1. Null / Undefined Tests (TS18047, TS18048, TS2531, TS2532, TS2533)
    # =========================================================================
    def test_ts18047_variable_possibly_null(self):
        raw = "user.ts(3,17): error TS18047: 'user' is possibly 'null'."
        res = self.engine.diagnose(raw, command="npx tsc user.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-null-undefined")
        self.assertIn("'user' is possibly 'null' (TS18047)", res.title)
        self.assertIn("strictNullChecks", res.explanation)
        self.assertTrue(any("user?.property" in s for s in res.suggestions))

    def test_ts18048_variable_possibly_undefined(self):
        raw = "config.ts(8,12): error TS18048: 'settings' is possibly 'undefined'."
        res = self.engine.diagnose(raw, command="npx tsc config.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-null-undefined")
        self.assertIn("'settings' is possibly 'undefined' (TS18048)", res.title)
        self.assertTrue(any("settings?.property" in s for s in res.suggestions))

    def test_ts2531_object_possibly_null(self):
        raw = "dom.ts(14,5): error TS2531: Object is possibly 'null'."
        res = self.engine.diagnose(raw, command="npx tsc dom.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-null-undefined")
        self.assertIn("Object is possibly 'null' (TS2531)", res.title)

    def test_ts2532_object_possibly_undefined(self):
        raw = "list.ts(2,8): error TS2532: Object is possibly 'undefined'."
        res = self.engine.diagnose(raw, command="npx tsc list.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-null-undefined")
        self.assertIn("Object is possibly 'undefined' (TS2532)", res.title)

    # =========================================================================
    # 2. Readonly & Constant Assignment Tests (TS2540, TS2588)
    # =========================================================================
    def test_ts2540_readonly_property_assignment(self):
        raw = "model.ts(28,6): error TS2540: Cannot assign to 'id' because it is a read-only property."
        res = self.engine.diagnose(raw, command="npx tsc model.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-readonly-assignment")
        self.assertIn("Cannot assign to 'id' because it is a read-only property (TS2540)", res.title)
        self.assertIn("readonly", res.explanation)
        self.assertTrue(any("readonly" in s for s in res.suggestions))

    def test_ts2588_const_variable_assignment(self):
        raw = "counter.ts(5,1): error TS2588: Cannot assign to 'total' because it is a constant."
        res = self.engine.diagnose(raw, command="npx tsc counter.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-readonly-assignment")
        self.assertIn("Cannot assign to 'total' because it is a constant (TS2588)", res.title)
        self.assertTrue(any("let total" in s for s in res.suggestions))

    # =========================================================================
    # 3. Missing Return Tests (TS2355, TS2366, TS7030)
    # =========================================================================
    def test_ts2355_function_must_return_value(self):
        raw = "calc.ts(7,24): error TS2355: A function whose declared type is neither 'undefined', 'void', nor 'any' must return a value."
        res = self.engine.diagnose(raw, command="npx tsc calc.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-missing-return")
        self.assertIn("Function is missing a return statement (TS2355)", res.title)
        self.assertTrue(any("return" in s for s in res.suggestions))

    def test_ts2366_lacks_ending_return(self):
        raw = "helper.ts(12,18): error TS2366: Function lacks ending return statement and return type does not include 'undefined'."
        res = self.engine.diagnose(raw, command="npx tsc helper.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-missing-return")
        self.assertIn("TS2366", res.title)

    def test_ts7030_not_all_code_paths_return(self):
        raw = "branch.ts(10,5): error TS7030: Not all code paths return a value."
        res = self.engine.diagnose(raw, command="npx tsc branch.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-missing-return")
        self.assertIn("TS7030", res.title)

    # =========================================================================
    # 4. Class Inheritance & Interface Implementation Tests (TS2420, TS2515, TS2416)
    # =========================================================================
    def test_ts2420_incorrectly_implements_interface(self):
        raw = (
            "athlete.ts(16,7): error TS2420: Class 'Athlete' incorrectly implements interface 'Runner'.\n"
            "  Property 'speed' is missing in type 'Athlete' but required in type 'Runner'."
        )
        res = self.engine.diagnose(raw, command="npx tsc athlete.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-class-inheritance")
        self.assertIn("Class 'Athlete' incorrectly implements interface 'Runner' (TS2420)", res.title)
        self.assertIn("Athlete", res.explanation)
        self.assertTrue(any("Runner" in s for s in res.suggestions))

    def test_ts2515_does_not_implement_abstract_member(self):
        raw = "dog.ts(14,7): error TS2515: Non-abstract class 'Dog' does not implement inherited abstract member makeSound from class 'Animal'."
        res = self.engine.diagnose(raw, command="npx tsc dog.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-class-inheritance")
        self.assertIn("Class 'Dog' does not implement abstract member 'makeSound' (TS2515)", res.title)
        self.assertIn("Animal", res.explanation)
        self.assertTrue(any("makeSound" in s for s in res.suggestions))

    def test_ts2416_property_incompatible_with_base(self):
        raw = (
            "sub.ts(21,5): error TS2416: Property 'id' in type 'Sub' is not assignable to the same property in base type 'Base'.\n"
            "  Type 'string' is not assignable to type 'number'."
        )
        res = self.engine.diagnose(raw, command="npx tsc sub.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-class-inheritance")
        self.assertIn("Property 'id' in 'Sub' is incompatible with base 'Base' (TS2416)", res.title)
        self.assertTrue(any("Base" in s or "Sub" in s for s in res.suggestions))

    # =========================================================================
    # 5. Generic Type Parameter Constraint Tests (TS2344)
    # =========================================================================
    def test_ts2344_type_constraint_violation(self):
        raw = "generic.ts(35,9): error TS2344: Type 'number' does not satisfy the constraint 'HasLength'."
        res = self.engine.diagnose(raw, command="npx tsc generic.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-type-constraint")
        self.assertIn("Type 'number' does not satisfy constraint 'HasLength' (TS2344)", res.title)
        self.assertIn("HasLength", res.explanation)
        self.assertTrue(any("HasLength" in s for s in res.suggestions))

    # =========================================================================
    # 6. Async & Await Usage Tests (TS1308, TS1375)
    # =========================================================================
    def test_ts1308_await_in_non_async_function(self):
        raw = "async.ts(39,5): error TS1308: 'await' expressions are only allowed within async functions and at the top levels of modules."
        res = self.engine.diagnose(raw, command="npx tsc async.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-async-await")
        self.assertIn("'await' used outside async function or module context (TS1308)", res.title)
        self.assertTrue(any("async" in s for s in res.suggestions))

    def test_ts1375_top_level_await_non_module(self):
        raw = "script.ts(1,1): error TS1375: 'await' expressions are only allowed at the top level of a file when that file is a module, but this file has no imports or exports."
        res = self.engine.diagnose(raw, command="npx tsc script.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-async-await")
        self.assertIn("TS1375", res.title)
        self.assertTrue(any("export {};" in s for s in res.suggestions))

    # =========================================================================
    # 7. Location Extraction & Invariant Tests
    # =========================================================================
    def test_extract_location_ts18047(self):
        raw = "src/services/auth.ts(102,15): error TS18047: 'token' is possibly 'null'."
        loc = ErrorParser.extract_location(raw)
        self.assertIsNotNone(loc)
        self.assertIn("auth.ts", loc.file)
        self.assertEqual(loc.line, 102)
        self.assertEqual(loc.column, 15)

    def test_generic_python_and_js_errors_unaffected(self):
        raw_py = "ZeroDivisionError: division by zero"
        res_py = self.engine.diagnose(raw_py, command="python math.py", exit_code=1)
        self.assertEqual(res_py.rule_id, "zero-division-error")

        raw_js = "ReferenceError: require is not defined\n    at test.js:1:1"
        res_js = self.engine.diagnose(raw_js, command="node test.js", exit_code=1)
        self.assertEqual(res_js.rule_id, "js-reference-error")

    def test_all_48_rules_registered_and_unique(self):
        rules = self.engine.registry.all_rules()
        self.assertEqual(len(rules), 48)
        self.assertEqual(len(BUILTIN_RULES), 48)

        rule_ids = [r.rule_id for r in rules]
        self.assertEqual(len(rule_ids), len(set(rule_ids)))

if __name__ == "__main__":
    unittest.main()
