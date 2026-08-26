"""Tests for scripts/sheets_queue.py (Issue #13 — Queue stage, spec §8)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.csv_to_geojson import SCHEMA  # noqa: E402
from scripts.sheets_queue import (  # noqa: E402
    append_rows, main as queue_main, read_tab, row_from_extraction, sheet_api_url)


class TestRowFromExtraction(unittest.TestCase):
    def test_maps_extraction_to_schema_order(self):
        extraction = {"name": "Foo DC", "capacity_mw": "50"}
        row = row_from_extraction(extraction, today="2026-08-26")
        self.assertEqual(len(row), len(SCHEMA))
        self.assertEqual(row[SCHEMA.index("name")], "Foo DC")
        self.assertEqual(row[SCHEMA.index("capacity_mw")], "50")

    def test_defaults_verification_status_to_needs_review(self):
        row = row_from_extraction({"name": "X"}, today="2026-08-26")
        self.assertEqual(row[SCHEMA.index("verification_status")], "needs review")
        self.assertEqual(row[SCHEMA.index("last_updated")], "2026-08-26")


class TestSheetApiUrl(unittest.TestCase):
    def test_builds_values_append_endpoint_and_quotes_tab_name(self):
        url = sheet_api_url("SHEET123", "Pending")
        self.assertTrue(url.startswith(
            "https://sheets.googleapis.com/v4/spreadsheets/SHEET123/values/"))
        self.assertIn("Pending", url)
        self.assertIn("valueInputOption=RAW", url)
        self.assertIn("insertDataOption=INSERT_ROWS", url)


class TestAppendRows(unittest.TestCase):
    def test_posts_rows_and_returns_response(self):
        calls = []

        def fake_transport(method, url, body):
            calls.append((method, url, body))
            return {"updates": {"updatedRows": 2}}

        resp = append_rows(fake_transport, "SHEET123", "Pending",
                           [row_from_extraction({"name": "A"}, today="t"),
                            row_from_extraction({"name": "B"}, today="t")])
        self.assertEqual(resp["updates"]["updatedRows"], 2)
        method, url, body = calls[0]
        self.assertEqual(method, "POST")
        self.assertIn("SHEET123", url)
        self.assertEqual(len(body["values"]), 2)

    def test_transport_error_propagates_for_caller_to_log(self):
        def boom(method, url, body):
            raise OSError("401 unauthorized")
        with self.assertRaises(OSError):
            append_rows(boom, "S", "Pending", [["a"]])

    def test_append_to_main_is_a_hard_rail(self):
        def never_called(method, url, body):
            raise AssertionError("must not call the API for Main")
        with self.assertRaises(ValueError):
            append_rows(never_called, "S", "Main", [["a"]])
        with self.assertRaises(ValueError):
            append_rows(never_called, "S", " MAIN ", [["a"]])


class TestReadTab(unittest.TestCase):
    def test_returns_values_or_empty_list(self):
        t = lambda m, u, b: {"values": [["name"], ["A"]]}
        self.assertEqual(read_tab(t, "S", "Pending"), [["name"], ["A"]])
        t2 = lambda m, u, b: {}
        self.assertEqual(read_tab(t2, "S", "Pending"), [])


class TestQueueCli(unittest.TestCase):
    def test_queues_only_new_rows_deduped_against_sheet(self):
        import json, tempfile
        calls = []
        header = list(SCHEMA)
        existing = list(SCHEMA)
        existing[0] = "Old DC"; existing[2] = "Kulai, Johor"

        def transport(method, url, body):
            if method == "GET":
                return {"values": [header, existing]}
            calls.append(body)
            return {"updates": {"updatedRows": len(body["values"])}}

        rows = [{"name": "Old DC", "address": "kulai, johor"},
                {"name": "New DC", "address": "Cyberjaya"}]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"rows": rows, "skipped": []}, f)
            path = f.name
        import contextlib, io, os as _os
        _os.environ["SHEET_ID"] = "S"
        with contextlib.redirect_stdout(io.StringIO()):
            rc = queue_main(["x", "--extraction", path], transport_factory=lambda: transport)
        _os.unlink(path)
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 1)
        appended = calls[0]["values"]
        self.assertEqual(len(appended), 1)
        self.assertEqual(appended[0][SCHEMA.index("name")], "New DC")


if __name__ == "__main__":
    unittest.main()
