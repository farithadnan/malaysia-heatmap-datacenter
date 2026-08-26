"""Tests for scripts/csv_to_geojson.py (Issue #5).

Spec §5 schema rows -> GeoJSON FeatureCollection for the Leaflet map.
"""
import csv
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.csv_to_geojson import convert_csv, row_to_feature  # noqa: E402

SCHEMA = ["name", "operator", "address", "latitude", "longitude", "capacity_mw",
          "capacity_type", "capacity_source", "status", "connection_voltage",
          "verification_status", "last_updated", "report_url"]


def make_row(**overrides):
    row = {k: "" for k in SCHEMA}
    row.update(overrides)
    return row


class TestRowToFeature(unittest.TestCase):
    def test_valid_row_becomes_point_feature(self):
        row = make_row(name="NEXTDC KL1", latitude="3.0946929", longitude="101.6284258")
        feature = row_to_feature(row)
        self.assertEqual(feature["type"], "Feature")
        self.assertEqual(feature["geometry"]["type"], "Point")
        # GeoJSON order is [longitude, latitude]
        self.assertEqual(feature["geometry"]["coordinates"], [101.6284258, 3.0946929])

    def test_all_13_schema_fields_carried_into_properties(self):
        row = make_row(name="NEXTDC KL1", operator="NEXTDC Sdn Bhd",
                       latitude="3.0946929", longitude="101.6284258",
                       capacity_mw="65", capacity_type="confirmed")
        props = row_to_feature(row)["properties"]
        for field in SCHEMA:
            self.assertIn(field, props)

    def test_capacity_mw_is_numeric_when_parseable(self):
        row = make_row(latitude="1", longitude="2", capacity_mw="72")
        self.assertEqual(row_to_feature(row)["properties"]["capacity_mw"], 72.0)

    def test_capacity_mw_is_null_when_blank(self):
        row = make_row(latitude="1", longitude="2", capacity_mw="")
        self.assertIsNone(row_to_feature(row)["properties"]["capacity_mw"])

    def test_row_without_coordinates_returns_none(self):
        row = make_row(name="No Coord DC")
        self.assertIsNone(row_to_feature(row))

    def test_row_with_unparseable_coordinates_returns_none(self):
        row = make_row(name="Bad Coord DC", latitude="north", longitude="east")
        self.assertIsNone(row_to_feature(row))


class TestConvertCsv(unittest.TestCase):
    def _write_csv(self, path, rows):
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=SCHEMA)
            w.writeheader()
            w.writerows(rows)

    def test_skips_rows_without_coordinates_and_reports_them(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = os.path.join(d, "in.csv"), os.path.join(d, "out.geojson")
            self._write_csv(src, [
                make_row(name="Good", latitude="3.1", longitude="101.6"),
                make_row(name="MissingCoords"),
            ])
            counts = convert_csv(src, dst)
            self.assertEqual(counts["features"], 1)
            self.assertEqual(counts["skipped"], 1)
            self.assertTrue(any("MissingCoords" in w for w in counts["warnings"]))

    def test_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "in.csv")
            self._write_csv(src, [make_row(name="A", latitude="3.1", longitude="101.6"),
                                  make_row(name="B", latitude="1.5", longitude="103.6")])
            out1, out2 = os.path.join(d, "a.geojson"), os.path.join(d, "b.geojson")
            convert_csv(src, out1)
            convert_csv(src, out2)
            self.assertEqual(open(out1, "rb").read(), open(out2, "rb").read())

    def test_written_file_is_valid_feature_collection(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = os.path.join(d, "in.csv"), os.path.join(d, "out.geojson")
            self._write_csv(src, [make_row(name="A", latitude="3.1", longitude="101.6")])
            convert_csv(src, dst)
            with open(dst, encoding="utf-8") as f:
                doc = json.load(f)
            self.assertEqual(doc["type"], "FeatureCollection")
            self.assertEqual(len(doc["features"]), 1)


if __name__ == "__main__":
    unittest.main()
