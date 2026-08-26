"""Tests for scripts/github_queue.py (Queue stage, GitHub-native backend).

Owner decision 2026-08-26: the review queue lives in data/pending.csv +
auto-opened GitHub PRs (spec §9 alternative), not Google Sheets.
"""
import csv
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.csv_to_geojson import SCHEMA  # noqa: E402
from scripts.github_queue import (  # noqa: E402
    append_rows_to_csv, dedupe_new_rows, format_pr_body, queue_findings)


def row(name="Foo DC", address="Kulai, Johor", **kw):
    r = {k: "" for k in SCHEMA}
    r.update({"name": name, "address": address,
              "verification_status": "needs review"})
    r.update(kw)
    return r


class TestDedupeNewRows(unittest.TestCase):
    def test_new_row_is_kept(self):
        to_add, skipped = dedupe_new_rows([row()], [row(name="Bar DC")])
        self.assertEqual([r["name"] for r in to_add], ["Bar DC"])
        self.assertEqual(skipped, 0)

    def test_same_name_and_address_is_a_duplicate(self):
        to_add, skipped = dedupe_new_rows([row()], [row(name=" foo dc ")])
        self.assertEqual(to_add, [])
        self.assertEqual(skipped, 1)


class TestAppendRowsToCsv(unittest.TestCase):
    def test_appends_preserving_header_and_commas(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "pending.csv")
            append_rows_to_csv(path, [])
            append_rows_to_csv(path, [row(address="1 Jalan A, KL")])
            with open(path, newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["address"], "1 Jalan A, KL")


class TestFormatPrBody(unittest.TestCase):
    def test_lists_count_and_names(self):
        body = format_pr_body([row(name="A"), row(name="B")], run_date="2026-08-26")
        self.assertIn("2 new finding(s)", body)
        self.assertIn("A", body)
        self.assertIn("B", body)
        self.assertIn("2026-08-26", body)


class TestQueueFindings(unittest.TestCase):
    def test_full_flow_issues_expected_commands_and_returns_pr_url(self):
        with tempfile.TemporaryDirectory() as d:
            csv_path = os.path.join(d, "pending.csv")
            append_rows_to_csv(csv_path, [])
            cmds = []

            def execute(args):
                cmds.append(args[0] if isinstance(args, list) else args)
                for a in (args if isinstance(args, list) else [args]):
                    if "pr" in a and "create" in a:
                        return "https://github.com/x/y/pull/42\n"
                return ""

            url = queue_findings(csv_path, [row()], branch="queue/2026-08-26",
                                 run_date="2026-08-26", execute=execute)
            self.assertEqual(url, "https://github.com/x/y/pull/42")
            joined = " ".join(str(c) for c in cmds)
            for token in ["checkout", "commit", "push", "pr create"]:
                self.assertIn(token, joined)

    def test_no_findings_means_no_git_activity(self):
        cmds = []
        url = queue_findings("/tmp/nope.csv", [], branch="queue/x",
                             run_date="2026-08-26",
                             execute=lambda a: cmds.append(a) or "")
        self.assertIsNone(url)
        self.assertEqual(cmds, [])


if __name__ == "__main__":
    unittest.main()
