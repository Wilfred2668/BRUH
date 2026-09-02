"""Unit tests for the SessionStore and CommandContext."""

import unittest
import tempfile
from pathlib import Path
from bruh.capture.context import CommandContext
from bruh.capture.session import SessionStore

class TestSessionStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.session_file = Path(self.temp_dir.name) / "last_session.json"
        self.store = SessionStore(session_file=self.session_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load_session(self):
        ctx = CommandContext(
            command="npm run dev",
            exit_code=1,
            output="Error: listen EADDRINUSE: address already in use :::3000",
            cwd="/workspace/test",
            shell="bash"
        )
        saved = self.store.save(ctx)
        self.assertTrue(saved)
        self.assertTrue(self.session_file.exists())

        loaded = self.store.load()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.command, "npm run dev")
        self.assertEqual(loaded.exit_code, 1)
        self.assertIn("EADDRINUSE", loaded.output)
        self.assertEqual(loaded.cwd, "/workspace/test")
        self.assertEqual(loaded.shell, "bash")

    def test_load_nonexistent_session(self):
        loaded = self.store.load()
        self.assertIsNone(loaded)

    def test_corrupted_session_recovery(self):
        # Write corrupted JSON to session file
        self.session_file.write_text("{ this is not valid json : [[", encoding="utf-8")
        loaded = self.store.load()
        self.assertIsNone(loaded)

    def test_clear_session(self):
        ctx = CommandContext(command="pytest", exit_code=1)
        self.store.save(ctx)
        self.assertTrue(self.session_file.exists())
        self.store.clear()
        self.assertFalse(self.session_file.exists())

if __name__ == "__main__":
    unittest.main()
