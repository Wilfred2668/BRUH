"""Comprehensive tests for Phase 7 JavaScript / Node.js Diagnostic Support."""

import unittest
from bruh.engine.matcher import DiagnosticEngine
from bruh.engine.registry import get_default_registry
from bruh.engine.parser import ErrorParser

class TestJavaScriptDiagnostics(unittest.TestCase):

    def setUp(self):
        self.engine = DiagnosticEngine(registry=get_default_registry())

    # =========================================================================
    # 1. ReferenceError Tests
    # =========================================================================
    def test_reference_error_undefined_variable(self):
        raw = (
            "[eval]:1\n"
            "console.log(undefinedVariable)\n"
            "            ^\n"
            "ReferenceError: undefinedVariable is not defined\n"
            "    at [eval]:1:13\n"
            "    at runScriptInThisContext (node:internal/vm:219:10)"
        )
        res = self.engine.diagnose(raw, command="node script.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-reference-error")
        self.assertIn("undefinedVariable", res.title)
        self.assertIn("undefinedVariable", res.explanation)
        self.assertTrue(any("undefinedVariable" in s for s in res.suggestions))

    def test_reference_error_temporal_dead_zone(self):
        raw = (
            "ReferenceError: Cannot access 'apiKey' before initialization\n"
            "    at start (C:\\project\\config.js:15:9)"
        )
        res = self.engine.diagnose(raw, command="node config.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-reference-error")
        self.assertIn("apiKey", res.title)
        self.assertIn("Temporal Dead Zone", res.explanation)

    # =========================================================================
    # 2. TypeError Tests
    # =========================================================================
    def test_type_error_null_property_access(self):
        raw = (
            "TypeError: Cannot read properties of null (reading 'name')\n"
            "    at getUser (C:\\project\\user.js:24:18)"
        )
        res = self.engine.diagnose(raw, command="node user.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-type-error")
        self.assertIn("name", res.title)
        self.assertIn("null", res.title)
        self.assertTrue(any("?." in s for s in res.suggestions))

    def test_type_error_undefined_property_access(self):
        raw = (
            "TypeError: Cannot read properties of undefined (reading 'length')\n"
            "    at /var/www/app.js:50:22"
        )
        res = self.engine.diagnose(raw, command="node app.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-type-error")
        self.assertIn("length", res.title)
        self.assertIn("undefined", res.title)

    def test_type_error_not_a_function(self):
        raw = (
            "TypeError: user.authenticate is not a function\n"
            "    at login (C:\\project\\auth.js:33:10)"
        )
        res = self.engine.diagnose(raw, command="node auth.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-type-error")
        self.assertIn("user.authenticate", res.title)
        self.assertIn("not a function", res.title)

    def test_type_error_assignment_to_constant(self):
        raw = "TypeError: Assignment to constant variable.\n    at [eval]:1:7"
        res = self.engine.diagnose(raw, command="node test.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-type-error")
        self.assertIn("Assignment to constant variable", res.title)
        self.assertTrue(any("let" in s for s in res.suggestions))

    # =========================================================================
    # 3. SyntaxError Tests
    # =========================================================================
    def test_syntax_error_unexpected_token(self):
        raw = (
            "SyntaxError: Unexpected token '}'\n"
            "    at compileScript (node:internal/process/execution:388:10)"
        )
        res = self.engine.diagnose(raw, command="node bad_syntax.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-syntax-error")
        self.assertIn("Unexpected token '}'", res.title)

    def test_syntax_error_duplicate_declaration(self):
        raw = (
            "SyntaxError: Identifier 'count' has already been declared\n"
            "    at /home/user/app.js:10:5"
        )
        res = self.engine.diagnose(raw, command="node app.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-syntax-error")
        self.assertIn("Identifier 'count' has already been declared", res.title)

    # =========================================================================
    # 4. RangeError Tests
    # =========================================================================
    def test_range_error_call_stack_overflow(self):
        raw = (
            "RangeError: Maximum call stack size exceeded\n"
            "    at recurse (C:\\project\\tree.js:12:5)\n"
            "    at recurse (C:\\project\\tree.js:12:5)"
        )
        res = self.engine.diagnose(raw, command="node tree.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-range-error")
        self.assertIn("Maximum call stack size exceeded", res.title)
        self.assertTrue(any("base case" in s.lower() for s in res.suggestions))

    def test_range_error_invalid_array_length(self):
        raw = "RangeError: Invalid array length\n    at [eval]:1:5"
        res = self.engine.diagnose(raw, command="node arr.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-range-error")
        self.assertIn("Invalid array length", res.title)

    # =========================================================================
    # 5. Node.js Module Resolution Tests
    # =========================================================================
    def test_module_not_found_npm_package(self):
        raw = (
            "node:internal/modules/cjs/loader:1424\n"
            "  throw err;\n"
            "  ^\n"
            "Error: Cannot find module 'express'\n"
            "Require stack:\n"
            "- C:\\Users\\Admin\\project\\server.js\n"
            "{\n"
            "  code: 'MODULE_NOT_FOUND'\n"
            "}"
        )
        res = self.engine.diagnose(raw, command="node server.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-module-not-found")
        self.assertIn("express", res.title)
        self.assertTrue(any("npm install express" in s for s in res.suggestions))

    def test_module_not_found_local_file(self):
        raw = (
            "Error: Cannot find module './utils/helper'\n"
            "Require stack:\n"
            "- /var/www/index.js\n"
            "{\n"
            "  code: 'MODULE_NOT_FOUND'\n"
            "}"
        )
        res = self.engine.diagnose(raw, command="node index.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-module-not-found")
        self.assertIn("./utils/helper", res.title)
        self.assertIn("local", res.title.lower())
        self.assertTrue(any("relative path" in s for s in res.suggestions))

    # =========================================================================
    # 6. JSON Parse Error Tests
    # =========================================================================
    def test_json_parse_error_modern_node(self):
        raw = (
            "<anonymous_script>:1\n"
            "{\"name\":}\n"
            "        ^\n"
            "SyntaxError: Unexpected token '}', \"{\"name\":}\" is not valid JSON\n"
            "    at JSON.parse (<anonymous>)\n"
            "    at [eval]:1:6"
        )
        res = self.engine.diagnose(raw, command="node parse.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-json-parse-error")
        self.assertIn("JSON Parse Error", res.title)

    def test_json_parse_trailing_comma(self):
        raw = (
            "<anonymous_script>:1\n"
            "{\"name\":\"Alice\",}\n"
            "                 ^\n"
            "SyntaxError: Unexpected token '}', \"{\"name\":\"Alice\",}\" is not valid JSON\n"
            "    at JSON.parse (<anonymous>)\n"
            "    at [eval]:1:6"
        )
        res = self.engine.diagnose(raw, command="node index.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-json-parse-error")
        self.assertIn("JSON Parse Error", res.title)
        self.assertTrue(any("trailing comma" in s.lower() for s in res.suggestions))

    def test_json_parse_missing_value(self):
        raw = (
            "<anonymous_script>:1\n"
            "{\"name\":}\n"
            "        ^\n"
            "SyntaxError: Unexpected token '}', \"{\"name\":}\" is not valid JSON\n"
            "    at JSON.parse (<anonymous>)\n"
            "    at [eval]:1:6"
        )
        res = self.engine.diagnose(raw, command="node index.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-json-parse-error")
        self.assertIn("JSON Parse Error", res.title)

    def test_json_parse_object_coercion(self):
        raw = (
            "<anonymous_script>:1\n"
            "[object Object]\n"
            " ^\n"
            "SyntaxError: \"[object Object]\" is not valid JSON\n"
            "    at JSON.parse (<anonymous>)\n"
            "    at [eval]:1:6"
        )
        res = self.engine.diagnose(raw, command="node index.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-json-parse-error")
        self.assertIn("JSON Parse Error", res.title)
        self.assertIn("[object Object]", res.explanation)
        self.assertTrue(any("JSON.stringify" in s for s in res.suggestions))

    def test_json_parse_invalid_string(self):
        raw = (
            "<anonymous_script>:1\n"
            "not json\n"
            "    ^\n"
            "SyntaxError: Unexpected token 'o', \"not json\" is not valid JSON\n"
            "    at JSON.parse (<anonymous>)\n"
            "    at [eval]:1:6"
        )
        res = self.engine.diagnose(raw, command="node index.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-json-parse-error")
        self.assertIn("JSON Parse Error", res.title)

    def test_json_parse_unexpected_end_of_input(self):
        raw = (
            "SyntaxError: Unexpected end of JSON input\n"
            "    at JSON.parse (<anonymous>)\n"
            "    at [eval]:1:6"
        )
        res = self.engine.diagnose(raw, command="node parse.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-json-parse-error")
        self.assertIn("Unexpected end of JSON input", res.title)

    def test_json_parse_error_position_format(self):
        raw = "SyntaxError: Unexpected token } in JSON at position 15\n    at JSON.parse (<anonymous>)"
        res = self.engine.diagnose(raw, command="node test.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-json-parse-error")
        self.assertIn("position 15", res.title)

    def test_generic_syntax_error_not_stolen_by_json_parse(self):
        """Generic JavaScript syntax errors without JSON signatures must match JSSyntaxErrorRule."""
        raw = (
            "[eval]:1\n"
            "if (true { console.log('x') }\n"
            "         ^\n"
            "SyntaxError: Unexpected token '='\n"
            "    at wrapSafe (node:internal/modules/cjs/loader:1692:18)"
        )
        res = self.engine.diagnose(raw, command="node test.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "js-syntax-error")
        self.assertIn("SyntaxError", res.title)

    # =========================================================================
    # 7. Stack Location Extraction (Windows, POSIX, eval)
    # =========================================================================
    def test_extract_node_windows_location(self):
        raw = (
            "TypeError: Cannot read properties of null (reading 'id')\n"
            "    at Object.startServer (C:\\Users\\Admin\\project\\server.js:42:15)\n"
            "    at Module._compile (node:internal/modules/cjs/loader:1546:14)"
        )
        loc = ErrorParser.extract_location(raw)
        self.assertIsNotNone(loc)
        self.assertIn("server.js", loc.file)
        self.assertEqual(loc.line, 42)
        self.assertEqual(loc.column, 15)
        self.assertEqual(loc.function, "Object.startServer")

    def test_extract_node_posix_location(self):
        raw = (
            "ReferenceError: db is not defined\n"
            "    at connect (/var/www/api/database.js:105:20)\n"
            "    at node:internal/main/run_main_module:28:49"
        )
        loc = ErrorParser.extract_location(raw)
        self.assertIsNotNone(loc)
        self.assertEqual(loc.file, "/var/www/api/database.js")
        self.assertEqual(loc.line, 105)
        self.assertEqual(loc.column, 20)
        self.assertEqual(loc.function, "connect")

    # =========================================================================
    # 8. Priority & Conflict Resolution
    # =========================================================================
    def test_js_json_parse_wins_over_generic_syntax_error(self):
        raw = "SyntaxError: Unexpected token '}', \"{\"key\":}\" is not valid JSON"
        res = self.engine.diagnose(raw, command="node parse.js", exit_code=1)
        self.assertEqual(res.rule_id, "js-json-parse-error")

    def test_js_module_not_found_wins_over_generic(self):
        raw = "Error: Cannot find module 'axios'\ncode: 'MODULE_NOT_FOUND'"
        res = self.engine.diagnose(raw, command="node api.js", exit_code=1)
        self.assertEqual(res.rule_id, "js-module-not-found")

if __name__ == "__main__":
    unittest.main()
