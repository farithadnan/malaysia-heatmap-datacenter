"""Tests for scripts/pipeline_fetch.py (Issue #11 — Fetch stage, spec §8)."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.pipeline_fetch import (  # noqa: E402
    download, is_pdf, plan_downloads, run)

WATCH_FINDINGS = {
    "date": "2026-08-26",
    "articles": [
        {"title": "A", "link": "http://x/a", "published": "", "source_feed": "f1"},
        {"title": "B", "link": "http://x/b", "published": "", "source_feed": "f1"},
        {"title": "C", "link": "http://x/c", "published": "", "source_feed": "f2"},
    ],
    "pages_changed": [], "errors": [],
}


class TestPlanDownloads(unittest.TestCase):
    def test_all_articles_planned_on_first_run(self):
        plan = plan_downloads(WATCH_FINDINGS, state=set())
        self.assertEqual(len(plan), 3)

    def test_already_downloaded_links_are_not_replanned(self):
        plan = plan_downloads(WATCH_FINDINGS, state={"http://x/a", "http://x/c"})
        self.assertEqual([a["link"] for a in plan], ["http://x/b"])


class TestIsPdf(unittest.TestCase):
    def test_pdf_magic_bytes(self):
        self.assertTrue(is_pdf(b"%PDF-1.4\n..."))

    def test_html_is_not_pdf(self):
        self.assertFalse(is_pdf(b"<!DOCTYPE html><html>"))


class TestDownload(unittest.TestCase):
    def test_success_returns_content(self):
        content, err = download("http://x/a", fetcher=lambda url: b"data")
        self.assertEqual(content, b"data")
        self.assertIsNone(err)

    def test_failure_returns_error_not_exception(self):
        def boom(url):
            raise OSError("timeout")
        content, err = download("http://x/a", fetcher=boom)
        self.assertIsNone(content)
        self.assertIn("timeout", err)


class TestRun(unittest.TestCase):
    def test_run_saves_new_items_skips_seen_and_reports(self):
        with tempfile.TemporaryDirectory() as d:
            findings_path = os.path.join(d, "watch.json")
            with open(findings_path, "w") as f:
                json.dump(WATCH_FINDINGS, f)
            state_path = os.path.join(d, "state.json")
            with open(state_path, "w") as f:
                json.dump({"downloaded": ["http://x/b"]}, f)
            out_dir = os.path.join(d, "articles")

            def fetcher(url):
                if url == "http://x/c":
                    raise OSError("503")
                return b"%PDF-1.4 fake" if url == "http://x/a" else b"<html>"

            report = run(findings_path, state_path, out_dir, today="2026-08-26",
                         fetcher=fetcher)
            self.assertEqual(report["downloaded"], 1)
            self.assertEqual(report["skipped_seen"], 1)
            self.assertEqual(report["errors"], 1)
            saved = os.listdir(os.path.join(out_dir, "2026-08-26"))
            self.assertTrue(saved[0].endswith(".pdf"))

    def test_run_is_idempotent_second_time(self):
        with tempfile.TemporaryDirectory() as d:
            findings_path = os.path.join(d, "watch.json")
            with open(findings_path, "w") as f:
                json.dump(WATCH_FINDINGS, f)
            state_path = os.path.join(d, "state.json")
            out_dir = os.path.join(d, "articles")
            fetcher = lambda url: b"<html>x</html>"
            run(findings_path, state_path, out_dir, today="2026-08-26", fetcher=fetcher)
            report2 = run(findings_path, state_path, out_dir, today="2026-08-27", fetcher=fetcher)
            self.assertEqual(report2["downloaded"], 0)
            self.assertEqual(report2["skipped_seen"], 3)


if __name__ == "__main__":
    unittest.main()
