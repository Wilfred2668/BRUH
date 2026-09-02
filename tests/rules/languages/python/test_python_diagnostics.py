"""Comprehensive tests for Phase 3 Rule Engine & Diagnostic Quality."""

import unittest
from bruh.engine.matcher import DiagnosticEngine
from bruh.engine.registry import get_default_registry
from bruh.engine.parser import ErrorParser

class TestPythonDiagnostics(unittest.TestCase):

    def setUp(self):
        self.engine = DiagnosticEngine(registry=get_default_registry())

    # =========================================================================
    # 1. ZeroDivisionError Tests
    # =========================================================================
    def test_zero_division_error_standard(self):
        raw = "ZeroDivisionError: division by zero\nFile \"math_util.py\", line 12"
        res = self.engine.diagnose(raw, command="python math_util.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "zero-division-error")
        self.assertIn("ZeroDivisionError", res.title)
        self.assertIn("divide a number by zero", res.explanation.lower())
        self.assertTrue(any("denominator" in s.lower() for s in res.suggestions))

    def test_zero_division_error_modulo(self):
        raw = "ZeroDivisionError: integer division or modulo by zero"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "zero-division-error")

    # =========================================================================
    # 2. KeyError Tests
    # =========================================================================
    def test_key_error_quoted(self):
        raw = "KeyError: 'user_id'\nFile \"handler.py\", line 45"
        res = self.engine.diagnose(raw, command="python handler.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "key-error")
        self.assertIn("user_id", res.title)
        self.assertIn("user_id", res.explanation)
        self.assertTrue(any("get('user_id'" in s for s in res.suggestions))

    def test_key_error_unquoted_number(self):
        raw = "KeyError: 42"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "key-error")
        self.assertIn("42", res.title)

    # =========================================================================
    # 3. IndexError Tests
    # =========================================================================
    def test_index_error_list(self):
        raw = "IndexError: list index out of range\nFile \"app.py\", line 10"
        res = self.engine.diagnose(raw, command="python app.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "index-error")
        self.assertIn("list index out of range", res.title)
        self.assertIn("0-based", res.suggestions[0])

    def test_index_error_pop_empty(self):
        raw = "IndexError: pop from empty list"
        res = self.engine.diagnose(raw, command="python queue.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "index-error")
        self.assertIn("empty", res.explanation.lower())

    # =========================================================================
    # 4. NameError & ReferenceError Tests
    # =========================================================================
    def test_name_error_python(self):
        raw = "NameError: name 'total_count' is not defined\nFile \"calc.py\", line 8"
        res = self.engine.diagnose(raw, command="python calc.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "name-error")
        self.assertIn("total_count", res.title)
        self.assertIn("total_count", res.explanation)
        self.assertTrue(any("spelling" in s.lower() for s in res.suggestions))

    def test_unbound_local_error_python(self):
        raw = "UnboundLocalError: local variable 'counter' referenced before assignment"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "name-error")
        self.assertIn("counter", res.title)
        self.assertIn("referenced", res.explanation.lower())

    def test_reference_error_node(self):
        raw = "ReferenceError: myVariable is not defined\n    at index.js:14:5"
        res = self.engine.diagnose(raw, command="node index.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertIn(res.rule_id, ("name-error", "js-reference-error"))
        self.assertIn("myVariable", res.title)
        self.assertIn("myVariable", res.explanation)

    # =========================================================================
    # 5. TypeError Tests
    # =========================================================================
    def test_type_error_unsupported_operands(self):
        raw = "TypeError: unsupported operand type(s) for +: 'int' and 'str'\nFile \"test.py\", line 3"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "type-error")
        self.assertIn("+", res.title)
        self.assertIn("int", res.title)
        self.assertIn("str", res.title)
        self.assertIn("incompatible types", res.explanation.lower())

    def test_type_error_concat(self):
        raw = "TypeError: can only concatenate str (not \"int\") to str"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "type-error")
        self.assertIn("cannot concatenate 'int' to str", res.title)

    def test_type_error_argument_count(self):
        raw = "TypeError: add_user() takes 2 positional arguments but 3 were given"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "type-error")
        self.assertIn("add_user() argument count mismatch", res.title)
        self.assertIn("expects 2", res.explanation)

    def test_type_error_missing_argument(self):
        raw = "TypeError: process_payment() missing 1 required positional argument: 'amount'"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "type-error")
        self.assertIn("missing argument 'amount'", res.title)

    def test_type_error_not_callable(self):
        raw = "TypeError: 'list' object is not callable"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "type-error")
        self.assertIn("'list' is not callable", res.title)

    def test_type_error_not_a_function_node(self):
        raw = "TypeError: callback is not a function\n    at server.js:25:9"
        res = self.engine.diagnose(raw, command="node server.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertIn(res.rule_id, ("type-error", "js-type-error"))
        self.assertIn("callback", res.title)
        self.assertIn("not a function", res.title)

    # =========================================================================
    # 6. ValueError Tests
    # =========================================================================
    def test_value_error_invalid_int(self):
        raw = "ValueError: invalid literal for int() with base 10: 'hello'"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "value-error")
        self.assertIn("invalid int literal 'hello'", res.title)
        self.assertIn("non-numeric", res.explanation.lower())

    def test_value_error_cannot_convert_float(self):
        raw = "ValueError: could not convert string to float: 'abc'"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "value-error")
        self.assertIn("cannot convert 'abc' to float", res.title)

    def test_value_error_unpack_mismatch(self):
        raw = "ValueError: not enough values to unpack (expected 3, got 2)"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "value-error")
        self.assertIn("not enough values to unpack", res.title)
        self.assertIn("3 variables", res.explanation)
        self.assertIn("2 item(s)", res.explanation)

    def test_value_error_not_in_list(self):
        raw = "ValueError: 'target_item' is not in list"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "value-error")
        self.assertIn("'target_item' is not in list", res.title)

    # =========================================================================
    # 7. ImportError & Circular Import Disambiguation Tests
    # =========================================================================
    def test_import_error_cannot_import_name(self):
        """ImportError for missing object inside module must NOT be ModuleNotFoundRule."""
        raw = "ImportError: cannot import name 'nonexistent_function' from 'os'"
        res = self.engine.diagnose(raw, command="python app.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "import-error")
        self.assertIn("nonexistent_function", res.title)
        self.assertIn("os", res.title)
        self.assertIn("located the module 'os'", res.explanation)
        self.assertTrue(any("shadowing" in s.lower() for s in res.suggestions))

    def test_import_error_circular_import(self):
        raw = "ImportError: cannot import name 'User' from partially initialized module 'models' (most likely due to a circular import)"
        res = self.engine.diagnose(raw, command="python main.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "import-error")
        self.assertIn("Circular Import", res.title)
        self.assertIn("circular import occurred", res.explanation.lower())

if __name__ == "__main__":
    unittest.main()
