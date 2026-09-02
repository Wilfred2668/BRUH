"""Unit tests for the error parser and location extractor."""

import unittest
from bruh.engine.parser import ErrorParser
from bruh.presentation.ansi import strip_ansi
from tests.fixtures import sample_errors

class TestErrorParser(unittest.TestCase):

    def test_strip_ansi(self):
        text = "\x1b[31;1mError:\x1b[0m \x1b[33mSomething broke\x1b[0m"
        clean = strip_ansi(text)
        self.assertEqual(clean, "Error: Something broke")

    def test_clean_output_crlf(self):
        raw = "Line 1\r\nLine 2\rLine 3\n"
        cleaned = ErrorParser.clean_output(raw)
        self.assertEqual(cleaned, "Line 1\nLine 2\nLine 3")

    def test_extract_location_python(self):
        loc = ErrorParser.extract_location(sample_errors.PYTHON_MODULE_NOT_FOUND_PANDAS)
        self.assertIsNotNone(loc)
        self.assertEqual(loc.file, "app.py")
        self.assertEqual(loc.line, 15)

    def test_extract_location_node(self):
        loc = ErrorParser.extract_location(sample_errors.NODE_PORT_IN_USE)
        self.assertIsNotNone(loc)
        self.assertIn("server.js", loc.file)
        self.assertEqual(loc.line, 24)
        self.assertEqual(loc.column, 8)

    def test_extract_location_compiler(self):
        comp_output = "/home/dev/project/main.cpp:42:15: error: expected ';' before '}' token"
        loc = ErrorParser.extract_location(comp_output)
        self.assertIsNotNone(loc)
        self.assertEqual(loc.file, "/home/dev/project/main.cpp")
        self.assertEqual(loc.line, 42)
        self.assertEqual(loc.column, 15)

    def test_extract_location_typescript(self):
        ts_output = "src/components/App.tsx(55,12): error TS2304: Cannot find name 'foo'."
        loc = ErrorParser.extract_location(ts_output)
        self.assertIsNotNone(loc)
        self.assertEqual(loc.file, "src/components/App.tsx")
        self.assertEqual(loc.line, 55)
        self.assertEqual(loc.column, 12)

    def test_extract_error_headline(self):
        headline = ErrorParser.extract_error_headline(sample_errors.PYTHON_MODULE_NOT_FOUND_PANDAS)
        self.assertEqual(headline, "ModuleNotFoundError: No module named 'pandas'")

    def test_unicode_output_handling(self):
        unicode_err = "Error: 🔥 Unhandled unicode symbol in file 你好.py:20"
        cleaned = ErrorParser.clean_output(unicode_err)
        self.assertIn("🔥", cleaned)
        self.assertIn("你好.py", cleaned)

    def test_empty_output_handling(self):
        self.assertEqual(ErrorParser.clean_output(""), "")
        self.assertIsNone(ErrorParser.extract_location(""))
        self.assertEqual(ErrorParser.extract_error_headline(""), "")

if __name__ == "__main__":
    unittest.main()
