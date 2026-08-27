"""Cross-stage integration: Fetch output layout must be Extract's input
(review Critical #1 — the two stages were silently non-composable)."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.common import link_digest  # noqa: E402
from scripts.pipeline_fetch import run as fetch_run  # noqa: E402
from scripts.pipeline_extract import run_extraction  # noqa: E402

LINK_A = "http://news.example/article-a"
LINK_B = "http://news.example/article-b"

FINDINGS = {
    "date": "2026-08-26",
    "articles": [{"title": "A", "link": LINK_A, "published": "", "source_feed": "f"},
                 {"title": "B", "link": LINK_B, "published": "", "source_feed": "f"}],
    "pages_changed": [], "errors": [],
}

LOREM_A = "<html><body><p>YTL Power develops a 500MW park in Kulai, Johor.</p></body></html>"
LOREM_B = "<html><body><p>Cats are nice.</p></body></html>"


class TestFetchToExtractContract(unittest.TestCase):
    def test_fetch_output_is_extract_input_over_dated_layout(self):
        with tempfile.TemporaryDirectory() as d:
            findings_path = os.path.join(d, "watch.json")
            with open(findings_path, "w") as f:
                json.dump(FINDINGS, f)

            fetches = {LINK_A: LOREM_A.encode(), LINK_B: LOREM_B.encode()}
            fetch_run(findings_path, os.path.join(d, "dl-state.json"),
                      os.path.join(d, "articles"), today="2026-08-26",
                      fetcher=fetches.get)

            def fake_llm(prompt):
                if "500MW" in prompt:
                    return {"found": True, "name": "YTL Johor DC Park",
                            "operator": "YTL Power", "location": "Kulai, Johor",
                            "capacity_mw": 500, "capacity_type": "confirmed",
                            "status": "planned"}
                return {"found": False}

            # pass fetch's OUTPUT ROOT — extract must find the dated subdir
            result = run_extraction(os.path.join(d, "articles"), findings_path,
                                    fake_llm, today="2026-08-26")
            self.assertEqual(len(result["rows"]), 1)
            row = result["rows"][0]
            self.assertEqual(row["name"], "YTL Johor DC Park")
            self.assertEqual(row["capacity_mw"], "500")
            self.assertEqual(row["report_url"], LINK_A)   # provenance intact

    def test_digest_contract_is_shared(self):
        self.assertEqual(link_digest(LINK_A), link_digest(LINK_A))
        self.assertNotEqual(link_digest(LINK_A), link_digest(LINK_B))
        self.assertEqual(len(link_digest(LINK_A)), 12)


if __name__ == "__main__":
    unittest.main()
