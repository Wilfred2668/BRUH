"""Comprehensive tests for Phase 4 Diagnostic Coverage Expansion & Rule Hardening."""

import unittest
from bruh.engine.matcher import DiagnosticEngine
from bruh.engine.registry import get_default_registry

class TestDomainDiagnostics(unittest.TestCase):

    def setUp(self):
        self.engine = DiagnosticEngine(registry=get_default_registry())

    # =========================================================================
    # 1. JSONDecodeError Tests
    # =========================================================================
    def test_json_decode_error_python_line_col(self):
        raw = "json.decoder.JSONDecodeError: Expecting value: line 2 column 5 (char 12)\nFile \"parser.py\", line 15"
        res = self.engine.diagnose(raw, command="python parser.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "json-decode-error")
        self.assertIn("line 2, col 5", res.title)
        self.assertIn("line 2, column 5", res.explanation)
        self.assertTrue(any("double quotes" in s.lower() for s in res.suggestions))

    def test_json_decode_error_python_generic(self):
        raw = "JSONDecodeError: Unterminated string starting at line 1 column 1 (char 0)"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "json-decode-error")
        self.assertIn("Unterminated string", res.title)

    def test_json_decode_error_node_unexpected_token(self):
        raw = "SyntaxError: Unexpected token ' in JSON at position 4\n    at JSON.parse (<anonymous>)"
        res = self.engine.diagnose(raw, command="node index.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertIn(res.rule_id, ("json-decode-error", "js-json-parse-error"))
        self.assertIn("position 4", res.title)
        self.assertIn("position 4", res.explanation)

    def test_json_decode_error_node_expected_token(self):
        raw = "SyntaxError: Expected property name or '}' in JSON at position 10"
        res = self.engine.diagnose(raw, command="node index.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertIn(res.rule_id, ("json-decode-error", "js-json-parse-error"))
        self.assertIn("JSON Parse Error", res.title)

    # =========================================================================
    # 2. SubprocessError Tests
    # =========================================================================
    def test_subprocess_called_process_error(self):
        raw = "subprocess.CalledProcessError: Command 'git clone https://repo' returned non-zero exit status 128."
        res = self.engine.diagnose(raw, command="python deploy.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "subprocess-error")
        self.assertIn("exit code 128", res.title)
        self.assertIn("git clone", res.title)
        self.assertIn("128", res.explanation)
        self.assertTrue(any("manually in your terminal" in s for s in res.suggestions))

    def test_subprocess_timeout_expired(self):
        raw = "subprocess.TimeoutExpired: Command 'ffmpeg -i video.mp4 output.avi' timed out after 30.0 seconds"
        res = self.engine.diagnose(raw, command="python transcode.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "subprocess-error")
        self.assertIn("TimeoutExpired", res.title)
        self.assertIn("30.0s", res.title)
        self.assertIn("30.0s", res.explanation)
        self.assertTrue(any("increase the timeout" in s.lower() for s in res.suggestions))

    # =========================================================================
    # 3. RecursionError & Call Stack Size Tests
    # =========================================================================
    def test_recursion_error_python(self):
        raw = "RecursionError: maximum recursion depth exceeded while calling a Python object\nFile \"tree.py\", line 42"
        res = self.engine.diagnose(raw, command="python tree.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "recursion-error")
        self.assertIn("RecursionError", res.title)
        self.assertIn("base case", res.explanation.lower())
        self.assertTrue(any("base case" in s.lower() for s in res.suggestions))

    def test_range_error_node_call_stack(self):
        raw = "RangeError: Maximum call stack size exceeded\n    at factorial (index.js:5:12)"
        res = self.engine.diagnose(raw, command="node index.js", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertIn(res.rule_id, ("recursion-error", "js-range-error"))
        self.assertIn("call stack", res.title.lower())
        self.assertIn("RangeError", res.title)

    # =========================================================================
    # 4. HTTP Client Error Tests
    # =========================================================================
    def test_http_client_requests_connection_error(self):
        raw = "requests.exceptions.ConnectionError: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded with url: /api"
        res = self.engine.diagnose(raw, command="python client.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "http-client-error")
        self.assertIn("Connection Failed", res.title)

    def test_http_client_requests_timeout(self):
        raw = "requests.exceptions.ReadTimeout: HTTPSConnectionPool(host='api.github.com', port=443): Read timed out. (read timeout=5)"
        res = self.engine.diagnose(raw, command="python fetch.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "http-client-error")
        self.assertIn("Timeout", res.title)

    def test_http_client_httpx_timeout(self):
        raw = "httpx.ReadTimeout: The read operation timed out"
        res = self.engine.diagnose(raw, command="python fetch.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "http-client-error")
        self.assertIn("Timeout", res.title)

    def test_http_client_urllib_error(self):
        raw = "urllib.error.URLError: <urlopen error [Errno 11001] getaddrinfo failed>"
        res = self.engine.diagnose(raw, command="python fetch.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "http-client-error")
        self.assertIn("Connection Failed", res.title)

    # =========================================================================
    # 5. AttributeError "Did You Mean" & CPython 3.10+ Tests
    # =========================================================================
    def test_attribute_error_did_you_mean(self):
        raw = "AttributeError: 'list' object has no attribute 'appendd'. Did you mean: 'append'?"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "runtime-attribute-error")
        self.assertTrue(any("append" in s for s in res.suggestions))

    def test_attribute_error_module_attribute(self):
        raw = "AttributeError: module 'math' has no attribute 'fast_sin'"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "runtime-attribute-error")
        self.assertIn("math", res.title)
        self.assertIn("fast_sin", res.title)

    def test_attribute_error_type_object(self):
        raw = "AttributeError: type object 'User' has no attribute 'find_by_email'"
        res = self.engine.diagnose(raw, command="python test.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "runtime-attribute-error")
        self.assertIn("User", res.title)

    # =========================================================================
    # 6. Priority & Conflict Disambiguation Tests
    # =========================================================================
    def test_json_decode_error_not_stolen_by_syntax_error(self):
        """JSON syntax error must match JSONDecodeErrorRule / JSJSONParseErrorRule, not generic SyntaxErrorRule."""
        raw = "SyntaxError: Unexpected token } in JSON at position 15"
        res = self.engine.diagnose(raw, command="node test.js", exit_code=1)
        self.assertIn(res.rule_id, ("json-decode-error", "js-json-parse-error"))

    def test_node_range_error_not_stolen_by_unknown(self):
        raw = "RangeError: Maximum call stack size exceeded"
        res = self.engine.diagnose(raw, command="node test.js", exit_code=1)
        self.assertIn(res.rule_id, ("recursion-error", "js-range-error"))

    def test_subprocess_called_process_error_list_format(self):
        """Python subprocess.CalledProcessError with list representation of arguments must match and be cleanly extracted."""
        raw = "subprocess.CalledProcessError: Command '['git', 'status_invalid_flag_xyz']' returned non-zero exit status 1."
        res = self.engine.diagnose(raw, command="python script.py", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "subprocess-error")
        self.assertIn("git status_invalid_flag_xyz", res.title)
        self.assertIn("exit code 1", res.title)

    def test_recursion_error_standard(self):
        """Standard Python RecursionError must match RecursionErrorRule."""
        raw = "Traceback (most recent call last):\n  File \"<string>\", line 1, in f\nRecursionError: maximum recursion depth exceeded"
        res = self.engine.diagnose(raw, command="python -c 'def f(): f(); f()'", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "recursion-error")
        self.assertIn("maximum recursion depth exceeded", res.title)

    def test_attribute_error_list_length_suggestion(self):
        """When calling .lenght() on a list, Bruh must suggest using built-in len()."""
        raw = "AttributeError: 'list' object has no attribute 'lenght'"
        res = self.engine.diagnose(raw, command="python -c 'x = [1, 2]; x.lenght()'", exit_code=1)
        self.assertTrue(res.is_known)
        self.assertEqual(res.rule_id, "runtime-attribute-error")
        self.assertTrue(any("len(x)" in s for s in res.suggestions))

if __name__ == "__main__":
    unittest.main()
