"""Tests for scripts/env.py — minimal .env loader (.env per owner request)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.env import load_dotenv  # noqa: E402


class TestLoadDotenv(unittest.TestCase):
    def setUp(self):
        self._saved = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._saved)

    def test_missing_file_is_a_noop(self):
        self.assertEqual(load_dotenv("/nonexistent/.env"), {})

    def test_loads_key_values_and_skips_comments(self):
        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as f:
            f.write("# comment\n\nFOO=bar\nEMPTY=\nQUOTED=\"a b\"\n")
            path = f.name
        loaded = load_dotenv(path)
        os.unlink(path)
        self.assertEqual(loaded, {"FOO": "bar", "EMPTY": "", "QUOTED": "a b"})
        self.assertEqual(os.environ["FOO"], "bar")

    def test_does_not_override_existing_environment(self):
        os.environ["FOO"] = "preset"
        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as f:
            f.write("FOO=from-file\n")
            path = f.name
        load_dotenv(path)
        os.unlink(path)
        self.assertEqual(os.environ["FOO"], "preset")

    def test_unquoted_inline_comment_is_stripped(self):
        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as f:
            f.write('PROVIDER=openai   # anthropic | deepseek | openai\n'
                    'QUOTED="value with #_inside"\n')
            path = f.name
        loaded = load_dotenv(path)
        os.unlink(path)
        self.assertEqual(loaded["PROVIDER"], "openai")
        self.assertEqual(loaded["QUOTED"], "value with #_inside")


if __name__ == "__main__":
    unittest.main()
