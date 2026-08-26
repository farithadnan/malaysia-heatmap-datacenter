"""Convert a project CSV (spec §5 schema) to a GeoJSON FeatureCollection.

The single conversion point between storage and the map (spec §9):
the Leaflet frontend only ever reads the GeoJSON this script produces.

Usage:
    python3 scripts/csv_to_geojson.py <input.csv> <output.geojson>

Exit status is 0 even when rows are skipped — skips are warnings
(printed to stderr and returned in the counts), never silent drops
(Issue #5 acceptance).
"""
import csv
import json
import sys

SCHEMA = ["name", "operator", "address", "latitude", "longitude", "capacity_mw",
          "capacity_type", "capacity_source", "status", "connection_voltage",
          "verification_status", "last_updated", "report_url"]


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def row_to_feature(row):
    """One CSV row -> one GeoJSON Feature, or None if it has no usable coordinates."""
    lat = _to_float(row.get("latitude"))
    lon = _to_float(row.get("longitude"))
    if lat is None or lon is None:
        return None
    props = {field: (row.get(field) or "") for field in SCHEMA}
    props["capacity_mw"] = _to_float(row.get("capacity_mw"))
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": props,
    }


def convert_csv(input_path, output_path):
    """Convert CSV file -> GeoJSON file. Returns counts + warnings."""
    with open(input_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    features, warnings = [], []
    for i, row in enumerate(rows, start=1):
        feature = row_to_feature(row)
        if feature is None:
            identity = row.get("name") or row.get("address") or f"<row {i}>"
            warnings.append(f"skipped {identity}: missing/unparseable coordinates")
            continue
        features.append(feature)
    doc = {"type": "FeatureCollection", "features": features}
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return {"features": len(features), "skipped": len(warnings), "warnings": warnings}


def main(argv):
    if len(argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    counts = convert_csv(argv[1], argv[2])
    for warning in counts["warnings"]:
        print(f"warning: {warning}", file=sys.stderr)
    print(f"{argv[2]}: {counts['features']} features, {counts['skipped']} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
