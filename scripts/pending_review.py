"""Review helper for data/pending.csv (spec §12).

Ranks pending rows by how ready they are to verify and promote to main.csv,
so the human pass goes quickly. Tiers:
  A  street-level coordinates + operator + status + capacity (verify fast)
  B  has coordinates + operator, missing some fields
  C  coarse shared-centroid coordinates (must confirm exact site)
  D  no coordinates yet (needs manual geocoding/lookup)

Rejected rows are skipped. Output is stdout; nothing is written.
"""
import csv
import os
import sys
from collections import defaultdict

PENDING = os.path.join(os.path.dirname(__file__), "..", "data", "pending.csv")


def _load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _has(p, field):
    return bool((p.get(field) or "").strip())


def main(argv):
    pend = _load(PENDING)
    coords = defaultdict(list)
    for p in pend:
        if _has(p, "latitude") and _has(p, "longitude") and p["verification_status"] != "rejected":
            coords[(p["latitude"].strip(), p["longitude"].strip())].append(p["name"].strip())

    def classify(p):
        has_coord = _has(p, "latitude") and _has(p, "longitude")
        has_op = _has(p, "operator")
        has_status = _has(p, "status")
        has_mw = _has(p, "capacity_mw")
        if not has_coord:
            return "D", 0
        shared = len(coords[(p["latitude"].strip(), p["longitude"].strip())]) > 1
        if has_op and has_status and has_mw and not shared:
            return "A", 3
        if has_op and not shared:
            return "B", 2
        return "C", 1

    rows = [p for p in pend if p["verification_status"] != "rejected"]
    graded = [(tier, score, p) for p in rows for tier, score in [classify(p)]]
    graded.sort(key=lambda g: (-g[1], g[0], g[2]["name"].strip().lower()))

    print(f"Review queue: {len(rows)} rows (rejected rows excluded)\n")
    for tier, score, p in graded:
        name = (p["name"] or "").strip() or "(unnamed)"
        op = (p["operator"] or "").strip()
        st = (p["status"] or "").strip()
        mw = (p["capacity_mw"] or "").strip() + ((" " + p["capacity_type"].strip()) if p.get("capacity_type", "").strip() else "")
        coord = f"{p['latitude'].strip()},{p['longitude'].strip()}" if _has(p, "latitude") else "NO-COORD"
        flag = ""
        if tier in ("A",):
            flag = "  <-- verify + promote candidate"
        elif tier == "C":
            flag = "  (coarse centroid - confirm exact site)"
        elif tier == "D":
            flag = "  (needs geocoding)"
        print(f"[{tier}] {name[:40]:40} | {op[:22]:22} | {st[:18]:18} | {mw[:12]:12} | {coord:24}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
