"""Tests for scripts/sheets_queue.py (Issue #13 — Queue stage, spec §8)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.csv_to_geojson import SCHEMA  # noqa: E402
from scripts.sheets_queue import append_rows, sheet_api_url, row_from_extraction  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
