"""Tests for scripts/pipeline_watch.py (Issue #10 — Watch stage, spec §8)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.pipeline_watch import (  # noqa: E402
    dedupe_by_link, hash_text, parse_rss, run, snapshot_pages)

RSS_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Google News</title>
<item>
  <title>YTL plans 100MW data center in Johor - The Edge Malaysia</title>
  <link>https://news.google.com/rss/articles/AAA111</link>
  <pubDate>Mon, 25 Aug 2026 01:00:00 GMT</pubDate>
</item>
<item>
  <title>TNB signs supply deal for new Cyberjaya site</title>
  <link>https://news.google.com/rss/articles/BBB222</link>
  <pubDate>Tue, 26 Aug 2026 02:30:00 GMT</pubDate>
</item>
</channel></rss>"""


class TestParseRss(unittest.TestCase):
    def test_parses_all_items_with_core_fields(self):
        items = parse_rss(RSS_FIXTURE)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "YTL plans 100MW data center in Johor - The Edge Malaysia")
        self.assertEqual(items[0]["link"], "https://news.google.com/rss/articles/AAA111")
        self.assertEqual(items[0]["published"], "Mon, 25 Aug 2026 01:00:00 GMT")

    def test_returns_empty_list_for_empty_feed(self):
        self.assertEqual(parse_rss('<?xml version="1.0"?><rss version="2.0"><channel/></rss>'), [])

    def test_raises_on_malformed_xml(self):
        with self.assertRaises(ValueError):
            parse_rss("<rss><channel><item>")


class TestDedupeByLink(unittest.TestCase):
    def test_keeps_first_occurrence_per_link(self):
        items = [{"link": "a", "title": "1"}, {"link": "a", "title": "dup"}, {"link": "b", "title": "2"}]
        self.assertEqual([i["title"] for i in dedupe_by_link(items)], ["1", "2"])


class TestSnapshotPages(unittest.TestCase):
    def test_first_sight_counts_as_changed_and_updates_state(self):
        changed, new_state = snapshot_pages(
            [{"name": "MIDA", "url": "http://x/mida"}],
            {}, lambda url: "content v1")
        self.assertEqual([c["name"] for c in changed], ["MIDA"])
        self.assertEqual(new_state["MIDA"], hash_text("content v1"))

    def test_unchanged_content_not_flagged(self):
        _, state1 = snapshot_pages([{"name": "MIDA", "url": "u"}], {}, lambda u: "same")
        changed, _ = snapshot_pages([{"name": "MIDA", "url": "u"}], state1, lambda u: "same")
        self.assertEqual(changed, [])

    def test_changed_content_flagged(self):
        _, state1 = snapshot_pages([{"name": "MIDA", "url": "u"}], {}, lambda u: "v1")
        changed, _ = snapshot_pages([{"name": "MIDA", "url": "u"}], state1, lambda u: "v2")
        self.assertEqual([c["name"] for c in changed], ["MIDA"])


class TestRunErrorTolerance(unittest.TestCase):
    def test_failing_feed_is_recorded_and_others_continue(self):
        import json, tempfile
        config = {"rss_feeds": [{"name": "good", "url": "u1"}, {"name": "bad", "url": "u2"}],
                  "pages": []}

        def fetcher(url):
            if url == "u2":
                raise OSError("connection refused")
            return RSS_FIXTURE

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as cf:
            json.dump(config, cf)
        with tempfile.TemporaryDirectory() as d:
            findings, _ = run(cf.name, d + "/state.json", fetcher=fetcher)
        os.unlink(cf.name)
        self.assertEqual(len(findings["articles"]), 2)
        self.assertEqual(len(findings["errors"]), 1)
        self.assertIn("bad", findings["errors"][0])


if __name__ == "__main__":
    unittest.main()
