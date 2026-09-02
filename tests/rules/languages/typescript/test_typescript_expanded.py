"""Unit and regression tests for Phase 9 Expanded TypeScript Diagnostics."""

import unittest
from bruh.engine.matcher import DiagnosticEngine
from bruh.engine.parser import ErrorParser
from bruh.engine.registry import get_default_registry, BUILTIN_RULES
from bruh.rules.languages.typescript.types.ts_implicit_any import TSImplicitAnyRule
from bruh.rules.languages.typescript.types.ts_element_implicit_any import TSElementImplicitAnyRule
from bruh.rules.languages.typescript.types.ts_unintentional_comparison import TSUnintentionalComparisonRule
from bruh.rules.languages.typescript.types.ts_index_signature_mismatch import TSIndexSignatureMismatchRule
from bruh.rules.languages.typescript.types.ts_missing_required_property import TSMissingRequiredPropertyRule
from bruh.rules.languages.typescript.types.ts_type_mismatch import TSTypeMismatchRule
from bruh.rules.languages.typescript.types.ts_property_not_found import TSPropertyNotFoundRule

class TestTypeScriptExpandedDiagnostics(unittest.TestCase):

    def setUp(self):
        self.engine = DiagnosticEngine(registry=get_default_registry())

    # =========================================================================
    # 1. Enhanced Implicit Any Tests (TS7008, TS7006, TS7005, TS7034)
    # =========================================================================
    def test_ts7008_member_implicit_any(self):
        raw = "app.ts(3,5): error TS7008: Member 'prop' implicitly has an 'any' type."
        res = self.engine.diagnose(raw, command="tsc --noEmit --noImplicitAny app.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-implicit-any")
        self.assertIn("Member 'prop' implicitly has an 'any' type", res.title)
        self.assertIn("Class property/member 'prop'", res.explanation)
        self.assertTrue(any("explicit type annotation" in s for s in res.suggestions))

    def test_ts7006_parameter_implicit_any(self):
        raw = "handler.ts(10,18): error TS7006: Parameter 'payload' implicitly has an 'any' type."
        res = self.engine.diagnose(raw, command="tsc --noEmit app.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-implicit-any")
        self.assertIn("Parameter 'payload' implicitly has an 'any' type", res.title)
        self.assertIn("Function parameter 'payload'", res.explanation)

    def test_ts7005_variable_implicit_any(self):
        raw = "utils.ts(5,9): error TS7005: Variable 'result' implicitly has an 'any' type."
        res = self.engine.diagnose(raw, command="tsc --noEmit app.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-implicit-any")
        self.assertIn("Variable 'result' implicitly has an 'any' type", res.title)
        self.assertIn("Variable 'result' was declared without", res.explanation)

    def test_ts7034_variable_implicit_any_locations(self):
        raw = "math.ts(12,9): error TS7034: Variable 'total' implicitly has type 'any' in some locations where its type cannot be determined."
        res = self.engine.diagnose(raw, command="tsc --noEmit app.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-implicit-any")
        self.assertIn("total", res.title)

    # =========================================================================
    # 2. Element Implicit Any Indexing Tests (TS7053)
    # =========================================================================
    def test_ts7053_element_implicit_any_indexing(self):
        raw = (
            "index.ts(10,11): error TS7053: Element implicitly has an 'any' type because "
            "expression of type 'string' can't be used to index type '{ name: string; }'.\n"
            "  No index signature with a parameter of type 'string' was found on type '{ name: string; }'."
        )
        res = self.engine.diagnose(raw, command="tsc --noEmit app.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-element-implicit-any")
        self.assertIn("Element implicitly has an 'any' type", res.title)
        self.assertIn("name: string", res.explanation)
        self.assertTrue(any("keyof type assertion" in s for s in res.suggestions))
        self.assertTrue(any("index signature" in s for s in res.suggestions))

    def test_ts7053_no_index_signature_variant(self):
        raw = "data.ts(5,8): error TS7053: Element implicitly has an 'any' type because type 'Config' has no index signature."
        res = self.engine.diagnose(raw, command="tsc --noEmit app.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-element-implicit-any")
        self.assertIn("Config", res.title)

    # =========================================================================
    # 3. Unintentional Comparison Tests (TS2367)
    # =========================================================================
    def test_ts2367_unintentional_comparison(self):
        raw = "check.ts(14,5): error TS2367: This comparison appears to be unintentional because the types 'number' and 'string' have no overlap."
        res = self.engine.diagnose(raw, command="tsc --noEmit app.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-unintentional-comparison")
        self.assertIn("Unintentional comparison", res.title)
        self.assertIn("number", res.explanation)
        self.assertIn("string", res.explanation)
        self.assertTrue(any("Number(" in s or "String(" in s for s in res.suggestions))

    # =========================================================================
    # 4. Index Signature Mismatch Tests (TS2411)
    # =========================================================================
    def test_ts2411_index_signature_incompatible_property(self):
        raw = "schema.ts(19,5): error TS2411: Property 'id' of type 'number' is not assignable to 'string' index type 'string'."
        res = self.engine.diagnose(raw, command="tsc --noEmit app.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-index-signature-mismatch")
        self.assertIn("Property 'id' incompatible with 'string' index type 'string'", res.title)
        self.assertIn("Property 'id' has type 'number'", res.explanation)
        self.assertTrue(any("Widen the index signature" in s for s in res.suggestions))

    def test_ts2411_with_ts2322_precedence(self):
        raw = (
            "test_ts.ts:3:5 - error TS2411: Property 'port' of type 'number' is not assignable to 'string' index type 'string'.\n"
            "test_ts.ts:6:7 - error TS2322: Type '{ port: number; host: string; }' is not assignable to type 'Config'."
        )
        res = self.engine.diagnose(raw, command="npx tsc test_ts.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-index-signature-mismatch")
        self.assertIn("TS2411", res.title)
        self.assertIn("port", res.title)
        self.assertIn("number", res.explanation)

    def test_ts2552_cannot_find_name_preserves_code(self):
        raw = "app.ts(2,13): error TS2552: Cannot find name 'usernme'. Did you mean 'username'?"
        res = self.engine.diagnose(raw, command="npx tsc app.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-cannot-find-name")
        self.assertIn("Cannot find name 'usernme' (TS2552)", res.title)
        self.assertTrue(any("Did you mean 'username'?" in s for s in res.suggestions))

    def test_ts2304_cannot_find_name_preserves_code(self):
        raw = "app.ts(1,13): error TS2304: Cannot find name 'undefinedVariable'."
        res = self.engine.diagnose(raw, command="npx tsc app.ts --noEmit", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-cannot-find-name")
        self.assertIn("Cannot find name 'undefinedVariable' (TS2304)", res.title)

    # =========================================================================
    # 5. Missing Required Properties Tests (TS2741, TS2739)
    # =========================================================================
    def test_ts2741_single_missing_required_property(self):
        raw = "models.ts(27,7): error TS2741: Property 'age' is missing in type '{ name: string; }' but required in type 'SingleRequired'."
        res = self.engine.diagnose(raw, command="tsc --noEmit app.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-missing-required-property")
        self.assertIn("Property 'age' is missing", res.title)
        self.assertIn("SingleRequired", res.title)
        self.assertIn("SingleRequired", res.explanation)
        self.assertTrue(any("Add property 'age'" in s for s in res.suggestions))
        self.assertTrue(any("age?: ..." in s for s in res.suggestions))

    def test_ts2739_multi_missing_required_properties(self):
        raw = "models.ts(35,7): error TS2739: Type '{ name: string; }' is missing the following properties from type 'MultiRequired': age, email, and 2 more."
        res = self.engine.diagnose(raw, command="tsc --noEmit app.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-missing-required-property")
        self.assertIn("Missing required properties from 'MultiRequired'", res.title)
        self.assertIn("age, email", res.explanation)
        self.assertTrue(any("Partial<MultiRequired>" in s for s in res.suggestions))

    # =========================================================================
    # 6. Enhanced Type Mismatch & Property Tests (TS2322, TS2345, TS2339)
    # =========================================================================
    def test_ts2322_union_type_mismatch(self):
        raw = "api.ts(8,5): error TS2322: Type 'string | number' is not assignable to type 'boolean'."
        res = self.engine.diagnose(raw, command="tsc --noEmit app.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-type-mismatch")
        self.assertIn("string | number", res.title)
        self.assertIn("boolean", res.title)

    def test_ts2345_generic_argument_mismatch(self):
        raw = "fetcher.ts(15,20): error TS2345: Argument of type 'Promise<string>' is not assignable to parameter of type 'string'."
        res = self.engine.diagnose(raw, command="tsc --noEmit app.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-type-mismatch")
        self.assertIn("Promise<string>", res.title)
        self.assertIn("parameter 'string'", res.title)

    def test_ts2339_nested_object_property_missing(self):
        raw = "server.ts(22,14): error TS2339: Property 'port' does not exist on type '{ host: string; }'."
        res = self.engine.diagnose(raw, command="tsc --noEmit app.ts", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "ts-property-not-found")
        self.assertIn("Property 'port' does not exist on type '{ host: string; }'", res.title)

    # =========================================================================
    # 7. Location Extraction Tests for Phase 9 Diagnostics
    # =========================================================================
    def test_extract_location_ts2741(self):
        raw = "src/models/user.ts(45,12): error TS2741: Property 'id' is missing in type '{}' but required in type 'User'."
        loc = ErrorParser.extract_location(raw)
        self.assertIsNotNone(loc)
        self.assertIn("user.ts", loc.file)
        self.assertEqual(loc.line, 45)
        self.assertEqual(loc.column, 12)

    def test_extract_location_colon_ts7053(self):
        raw = "/app/src/lookup.ts:18:22 - error TS7053: Element implicitly has an 'any' type because type 'Map' has no index signature."
        loc = ErrorParser.extract_location(raw)
        self.assertIsNotNone(loc)
        self.assertEqual(loc.file, "/app/src/lookup.ts")
        self.assertEqual(loc.line, 18)
        self.assertEqual(loc.column, 22)

    # =========================================================================
    # 8. Non-Interference & Invariants
    # =========================================================================
    def test_generic_js_syntax_error_not_stolen(self):
        raw = "SyntaxError: Unexpected identifier 'foo'\n    at Object.<anonymous> (test.js:4:1)"
        res = self.engine.diagnose(raw, command="node test.js", exit_code=1)
        self.assertEqual(res.rule_id, "js-syntax-error")

    def test_python_key_error_not_stolen(self):
        raw = "KeyError: 'user_id'\nFile \"server.py\", line 45"
        res = self.engine.diagnose(raw, command="python server.py", exit_code=1)
        self.assertEqual(res.rule_id, "key-error")

    def test_all_42_rules_registered_and_unique(self):
        rules = self.engine.registry.all_rules()
        self.assertGreaterEqual(len(rules), 42)
        self.assertGreaterEqual(len(BUILTIN_RULES), 42)

        rule_ids = [r.rule_id for r in rules]
        self.assertEqual(len(rule_ids), len(set(rule_ids)))

if __name__ == "__main__":
    unittest.main()
