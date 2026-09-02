"""Comprehensive tests for Phase 2 Diagnostic Intelligence, Session Capture, and Boundary Hardening."""

import unittest
import sys
import io
import time
import tempfile
from pathlib import Path
from unittest.mock import patch

from bruh.engine.matcher import DiagnosticEngine
from bruh.engine.extractors import FactExtractor
from bruh.engine.parser import ErrorParser
from bruh.engine.registry import get_default_registry
from bruh.presentation.renderer import TerminalRenderer
from bruh.presentation.ansi import strip_ansi
from bruh.capture.context import CommandContext
from bruh.capture.session import SessionStore
from bruh.capture.history import (
    is_multiline_fragment,
    reconstruct_multiline,
    isolate_command_before_bruh
)
from bruh.cli import main

class TestSessionIntelligence(unittest.TestCase):

    def setUp(self):
        self.engine = DiagnosticEngine(registry=get_default_registry())

    # =========================================================================
    # 1. Fact Extraction Tests
    # =========================================================================
    def test_fact_extractor_ports(self):
        """Test dynamic port extraction across diverse formats."""
        self.assertEqual(FactExtractor.extract_port("listen EADDRINUSE :::3000"), 3000)
        self.assertEqual(FactExtractor.extract_port("Port 5173 is already in use"), 5173)
        self.assertEqual(FactExtractor.extract_port("Failed to bind to 0.0.0.0:8080"), 8080)
        self.assertEqual(FactExtractor.extract_port("address already in use 127.0.0.1:5432"), 5432)

    def test_fact_extractor_attributes(self):
        """Test missing attribute and null/undefined extraction."""
        t1, a1 = FactExtractor.extract_missing_attribute("'NoneType' object has no attribute 'get'")
        self.assertEqual(t1, "NoneType")
        self.assertEqual(a1, "get")

        t2, a2 = FactExtractor.extract_missing_attribute("TypeError: Cannot read properties of undefined (reading 'map')")
        self.assertEqual(t2, "undefined")
        self.assertEqual(a2, "map")

    def test_fact_extractor_databases(self):
        """Test database ecosystem detection."""
        self.assertEqual(FactExtractor.extract_database_type("psycopg2.OperationalError: password authentication failed"), "PostgreSQL")
        self.assertEqual(FactExtractor.extract_database_type("pymysql.err.OperationalError: Access denied for user 'root'"), "MySQL")
        self.assertEqual(FactExtractor.extract_database_type("Redis connection to 127.0.0.1:6379 failed"), "Redis")

    # =========================================================================
    # 2. Command Boundary Isolation & Pasted Multi-Command Input
    # =========================================================================
    def test_isolate_command_pasted_with_bruh(self):
        """Test that pasting python code or curl followed by bruh isolates the actual command."""
        pasted_1 = 'python -c "import definitely_missing_db_driver_12345"\nbruh'
        self.assertEqual(isolate_command_before_bruh(pasted_1), 'python -c "import definitely_missing_db_driver_12345"')

        pasted_2 = 'python -c "user = None; print(user.name)"\r\nbruh'
        self.assertEqual(isolate_command_before_bruh(pasted_2), 'python -c "user = None; print(user.name)"')

        pasted_3 = 'curl.exe -i https://httpbin.org/status/502\nbruh'
        self.assertEqual(isolate_command_before_bruh(pasted_3), 'curl.exe -i https://httpbin.org/status/502')

    def test_bruh_excluded_from_diagnostic_target(self):
        """A raw bruh command must never become the diagnostic target."""
        self.assertIsNone(isolate_command_before_bruh("bruh"))
        self.assertIsNone(isolate_command_before_bruh("bruh\nbruh"))

    # =========================================================================
    # 3. Noise Filter & Frame Extraction Tests
    # =========================================================================
    def test_noise_filtering_pip_and_npm(self):
        """Test that pip update notices and npm log paths are stripped from headline determination."""
        noisy_output = (
            "ERROR: Could not find a version that satisfies the requirement requests_bad_pkg\n"
            "[notice] A new release of pip is available: 24.0 -> 26.2.1\n"
            "[notice] To update, run: python.exe -m pip install --upgrade pip"
        )
        headline = ErrorParser.extract_error_headline(noisy_output)
        self.assertIn("requests_bad_pkg", headline)
        self.assertNotIn("notice", headline.lower())

    def test_user_code_frame_preferred_over_stdlib(self):
        """Test that user code location (<string>:1 or app.py:10) is preferred over socket.py:837."""
        trace = (
            'Traceback (most recent call last):\n'
            '  File "<string>", line 1, in <module>\n'
            '  File "C:\\Python312\\Lib\\socket.py", line 837, in create_connection\n'
            '    raise exceptions[0]\n'
            'TimeoutError: timed out'
        )
        loc = ErrorParser.extract_location(trace)
        self.assertIsNotNone(loc)
        self.assertEqual(loc.file, "<string>")
        self.assertEqual(loc.line, 1)

    # =========================================================================
    # 4. HTTP Status Codes with Exit Code 0 Tests
    # =========================================================================
    def test_http_502_bad_gateway_with_exit_code_0(self):
        """HTTP 502 with exit code 0 must diagnose HTTP error and NOT display You're good."""
        raw = "HTTP/1.1 502 Bad Gateway\nServer: cloudflare\nContent-Type: text/html"
        result = self.engine.diagnose(raw, command="curl.exe -i https://httpbin.org/status/502", exit_code=0)
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "http-error")
        self.assertIn("502", result.title)
        self.assertIn("Bad Gateway", result.title)
        self.assertIn("server", result.explanation.lower())

        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "last_session.json"
            store = SessionStore(session_file=session_file)
            store.save(CommandContext(
                command="curl.exe -i https://httpbin.org/status/502",
                exit_code=0,
                output=raw,
                timestamp=time.time()
            ))
            with patch("bruh.cli.LAST_SESSION_FILE", session_file):
                with patch("bruh.cli.get_last_command_from_history", return_value=(None, 0)):
                    with patch("sys.stdout", new=io.StringIO()) as fake_out:
                        with patch("sys.argv", ["bruh"]):
                            code = main()
                            self.assertEqual(code, 0)
                            out = strip_ansi(fake_out.getvalue())
                            self.assertNotIn("You're good", out)
                            self.assertIn("HTTP 502", out)
                            self.assertIn("Bad Gateway", out)

    def test_http_401_unauthorized_with_exit_code_0(self):
        """HTTP 401 with exit code 0 must diagnose HTTP 401 Unauthorized."""
        raw = "HTTP/2 401 Unauthorized\nWWW-Authenticate: Bearer realm=\"api\""
        result = self.engine.diagnose(raw, command="curl -i https://api.example.com/protected", exit_code=0)
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "http-error")
        self.assertIn("401", result.title)
        self.assertIn("authentication", result.explanation.lower())

    def test_http_504_gateway_timeout(self):
        """HTTP 504 Gateway Timeout diagnosis."""
        raw = "HTTP/1.1 504 Gateway Timeout\nServer: nginx"
        result = self.engine.diagnose(raw, command="curl.exe -i https://httpbin.org/status/504", exit_code=0)
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "http-error")
        self.assertIn("504", result.title)
        self.assertIn("timed out", result.explanation.lower())

    def test_http_403_forbidden(self):
        """HTTP 403 Forbidden diagnosis."""
        raw = "HTTP/1.1 403 Forbidden\nContent-Type: application/json"
        result = self.engine.diagnose(raw, command="curl.exe -i https://httpbin.org/status/403", exit_code=0)
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "http-error")
        self.assertIn("403", result.title)
        self.assertIn("permission", result.explanation.lower())

    # =========================================================================
    # 5. Network, DNS, and Connection Error Tests
    # =========================================================================
    def test_curl_dns_failure_not_classified_as_success(self):
        """curl: (6) Could not resolve host must diagnose DNS error and NOT say You're good."""
        raw = "curl: (6) Could not resolve host: example.com"
        result = self.engine.diagnose(raw, command="curl.exe -I https://example.com", exit_code=6)
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "connection-refused")
        self.assertIn("DNS Resolution Failed", result.title)
        self.assertIn("example.com", result.title)
        self.assertIn("could not resolve the domain name", result.explanation.lower())
        self.assertTrue(any("internet connection" in s.lower() for s in result.suggestions))

        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "last_session.json"
            store = SessionStore(session_file=session_file)
            store.save(CommandContext(
                command="curl.exe -I https://example.com",
                exit_code=6,
                output=raw,
                timestamp=time.time()
            ))
            with patch("bruh.cli.LAST_SESSION_FILE", session_file):
                with patch("bruh.cli.get_last_command_from_history", return_value=(None, 0)):
                    with patch("sys.stdout", new=io.StringIO()) as fake_out:
                        with patch("sys.argv", ["bruh"]):
                            code = main()
                            self.assertEqual(code, 0)
                            out = strip_ansi(fake_out.getvalue())
                            self.assertNotIn("You're good", out)
                            self.assertIn("DNS Resolution Failed", out)

    def test_connection_timeout_python(self):
        """Test Python connection timeout with host, port, and timeout extraction."""
        raw = (
            'Traceback (most recent call last):\n'
            '  File "<string>", line 1, in <module>\n'
            '  File "C:\\Python312\\Lib\\socket.py", line 837, in create_connection\n'
            'TimeoutError: timed out'
        )
        result = self.engine.diagnose(raw, command="python -c \"import socket; socket.create_connection(('10.255.255.1', 81), timeout=1)\"", exit_code=1)
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "connection-refused")
        self.assertIn("Connection Timeout", result.title)
        self.assertIn("10.255.255.1:81", result.title)
        self.assertIn("10.255.255.1:81", result.explanation)
        self.assertTrue(any("Check that 10.255.255.1:81 is running" in s for s in result.suggestions))

    def test_connection_reset_by_peer(self):
        """Test connection reset by peer (ECONNRESET)."""
        raw = "ConnectionResetError: [Errno 104] Connection reset by peer\n127.0.0.1:8000"
        result = self.engine.diagnose(raw, command="python client.py", exit_code=1)
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "connection-refused")
        self.assertIn("Connection Reset", result.title)
        self.assertIn("closed or crashed", result.explanation.lower())

    # =========================================================================
    # 6. Database & Disambiguation Tests
    # =========================================================================
    def test_missing_psycopg2_is_module_not_found_not_database_error(self):
        """ModuleNotFoundError for psycopg2 must be classified as module-not-found, NOT database error."""
        raw = "ModuleNotFoundError: No module named 'psycopg2'"
        result = self.engine.diagnose(raw, command="python test_pg.py", exit_code=1)
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "module-not-found")
        self.assertIn("psycopg2", result.explanation)
        self.assertTrue(any("pip install psycopg2" in s for s in result.suggestions))

    def test_sqlite_database_is_locked(self):
        """Test SQLite database is locked diagnosis and progressive suggestions."""
        raw = "sqlite3.OperationalError: database is locked"
        result = self.engine.diagnose(raw, command="python test_sqlite.py", exit_code=1)
        self.assertTrue(result.is_known)
        self.assertEqual(result.rule_id, "database-error")
        self.assertIn("Database Is Locked", result.title)
        self.assertIn("SQLite while another connection was holding a lock", result.explanation)
        self.assertEqual(result.suggestions[0], "Close the other program using the database.")
        self.assertEqual(result.suggestions[1], "Make sure another connection is not keeping a transaction open.")
        self.assertEqual(result.suggestions[2], "Add retry handling if simultaneous access is expected.")

    # =========================================================================
    # 7. Session Transitions & No Stale Diagnostic Leakage
    # =========================================================================
    def test_session_transition_error_a_then_error_b(self):
        """When Error A occurs then Error B occurs, Bruh MUST diagnose Error B."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "last_session.json"
            store = SessionStore(session_file=session_file)

            # Error A: Missing file
            store.save(CommandContext(
                command="python missing_file.py",
                exit_code=1,
                output="FileNotFoundError: [Errno 2] No such file or directory: 'missing_file.py'",
                timestamp=time.time() - 10.0
            ))

            # Error B: Database locked
            store.save(CommandContext(
                command="python db.py",
                exit_code=1,
                output="sqlite3.OperationalError: database is locked",
                timestamp=time.time()
            ))

            loaded = store.load()
            res = self.engine.diagnose(loaded.output, command=loaded.command, exit_code=loaded.exit_code)
            self.assertEqual(res.rule_id, "database-error")
            self.assertIn("Database Is Locked", res.title)

    def test_session_transition_error_then_success(self):
        """When Error A occurs then git status succeeds, Bruh says You're good."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "last_session.json"
            store = SessionStore(session_file=session_file)

            # Error A
            store.save(CommandContext(
                command="python broken.py",
                exit_code=1,
                output="TypeError: Cannot read properties of undefined",
                timestamp=time.time() - 5.0
            ))

            # Success: git status
            store.save(CommandContext(
                command="git status",
                exit_code=0,
                output="On branch main\nnothing to commit, working tree clean",
                timestamp=time.time()
            ))

            with patch("bruh.cli.LAST_SESSION_FILE", session_file):
                with patch("bruh.cli.get_last_command_from_history", return_value=(None, 0)):
                    with patch("sys.stdout", new=io.StringIO()) as fake_out:
                        with patch("sys.argv", ["bruh"]):
                            code = main()
                            self.assertEqual(code, 0)
                            out = strip_ansi(fake_out.getvalue())
                            self.assertIn("You're good", out)
                            self.assertIn("git status", out)

    def test_session_transition_known_then_unknown(self):
        """When a known error is followed by an unknown error, the unknown error must be diagnosed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "last_session.json"
            store = SessionStore(session_file=session_file)

            # Error A: Known module not found
            store.save(CommandContext(
                command="python a.py",
                exit_code=1,
                output="ModuleNotFoundError: No module named 'numpy'",
                timestamp=time.time() - 5.0
            ))

            # Error B: Unknown CustomException
            store.save(CommandContext(
                command="python b.py",
                exit_code=1,
                output="CustomUnmappedPanic: something crashed\nFile \"b.py\", line 4",
                timestamp=time.time()
            ))

            loaded = store.load()
            res = self.engine.diagnose(loaded.output, command=loaded.command, exit_code=loaded.exit_code)
            self.assertFalse(res.is_known)
            self.assertEqual(res.rule_id, "unknown")
            self.assertIn("CustomUnmappedPanic", res.original_error)

    # =========================================================================
    # 8. Multiline PowerShell & Here-String Safety
    # =========================================================================
    def test_multiline_powershell_safety(self):
        """Test here-string detection and fragment safety."""
        fragment = '"@ | Set-Content test.py'
        self.assertTrue(is_multiline_fragment(fragment))

        lines = [
            '@"',
            'import socket',
            'socket.create_connection(("127.0.0.1", 80))',
            '"@ | Set-Content test.py'
        ]
        reconstructed = reconstruct_multiline(lines, 3)
        self.assertTrue(reconstructed.startswith('@"'))
        self.assertTrue(reconstructed.endswith('Set-Content test.py'))

    def test_successful_here_string_shows_you_are_good(self):
        """Successful here-string with exit code 0 must show You're good and NOT capture warning."""
        cmd = '@"\nprint("hello")\n"@ | Set-Content test_here.py'
        self.assertFalse(is_multiline_fragment(cmd))

        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "last_session.json"
            store = SessionStore(session_file=session_file)
            store.save(CommandContext(
                command=cmd,
                exit_code=0,
                output="",
                timestamp=time.time()
            ))

            with patch("bruh.cli.LAST_SESSION_FILE", session_file):
                with patch("bruh.cli.get_last_command_from_history", return_value=(None, 0)):
                    with patch("sys.stdout", new=io.StringIO()) as fake_out:
                        with patch("sys.argv", ["bruh"]):
                            code = main()
                            self.assertEqual(code, 0)
                            out = strip_ansi(fake_out.getvalue())
                            self.assertIn("You're good", out)
                            self.assertNotIn("couldn't capture", out.lower())

    def test_failed_command_after_here_string_diagnosed(self):
        """When a failed command runs after a here-string, diagnose the failed command."""
        pasted = '@"\nprint("hello")\n"@ | Set-Content test_here.py\npython test_here_missing.py\nbruh'
        target = isolate_command_before_bruh(pasted)
        self.assertEqual(target, "python test_here_missing.py")

    def test_incomplete_here_string_shows_capture_warning(self):
        """Incomplete here-string fragment alone must show capture warning."""
        fragment = '"@ | Set-Content test.py'
        self.assertTrue(is_multiline_fragment(fragment))

        with tempfile.TemporaryDirectory() as tmpdir:
            session_file = Path(tmpdir) / "last_session.json"
            store = SessionStore(session_file=session_file)
            store.save(CommandContext(
                command=fragment,
                exit_code=1,
                output="",
                timestamp=time.time()
            ))

            with patch("bruh.cli.LAST_SESSION_FILE", session_file):
                with patch("bruh.cli.get_last_command_from_history", return_value=(None, 0)):
                    with patch("sys.stdout", new=io.StringIO()) as fake_out:
                        with patch("sys.argv", ["bruh"]):
                            code = main()
                            self.assertEqual(code, 0)
                            out = strip_ansi(fake_out.getvalue())
                            self.assertIn("couldn't capture the previous command reliably", out)

if __name__ == "__main__":
    unittest.main()
