"""Queue stage (spec §8, stage 4): write validated findings into the
Google Sheet's **Pending** tab via the Sheets API values:append endpoint.

Design notes:
- Transport is injected (method, url, body) -> dict, so all logic is
  testable offline. The real transport uses a Google service-account
  access token (see module docstring of make_transport).
- NEVER writes to Main; callers pass tab="Pending" (spec §8 gate).
- Auth material comes from environment/secrets, never committed
  (.gitignore already covers *-key.json).

Production usage (GitHub Actions, Issue #13):
    from scripts.sheets_queue import make_transport, append_rows
    transport = make_transport(service_account_info)
    append_rows(transport, sheet_id, "Pending", rows)

The heavy lifting (JWT/OAuth2) is delegated to `google-auth` when
available (installed via requirements.txt in Actions); a stdlib
urllib fallback POSTs with a pre-minted access token.
"""
import json
import os
import urllib.parse
import urllib.request

from scripts.csv_to_geojson import SCHEMA
from scripts.env import load_dotenv

SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"
# Public endpoint home (one place only). If Google moves it, we change it HERE.
SHEETS_API_BASE = "https://sheets.googleapis.com/v4/spreadsheets"


def row_from_extraction(extraction, today, source_url=None):
    """One extraction dict -> one row ordered exactly as spec §5 schema."""
    row = list(SCHEMA)
    values = {field: str(extraction.get(field, "") or "") for field in SCHEMA}
    if not values["verification_status"]:
        values["verification_status"] = "needs review"
    if not values["last_updated"]:
        values["last_updated"] = today
    if source_url and not values["capacity_source"]:
        values["capacity_source"] = source_url
    return [values[field] for field in row]


def sheet_api_url(sheet_id, tab):
    quoted = urllib.parse.quote(tab, safe="")
    return (f"{SHEETS_API_BASE}/{sheet_id}"
            f"/values/{quoted}:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS")


def append_rows(transport, sheet_id, tab, rows):
    """Append rows to `tab` of the sheet. Returns the API response dict.

    Hard rail for the project's cardinal rule (spec §8): automation must
    NEVER write to Main — regardless of what a caller asks for.
    """
    if tab.strip().lower() == "main":
        raise ValueError("automation writes to Pending only — never Main (spec §8)")
    return transport("POST", sheet_api_url(sheet_id, tab), {"values": rows})


def make_transport(service_account_info=None):
    """Build the authorized (method, url, body) -> dict transport.

    service_account_info: parsed JSON of the service-account key.
    Requires the `google-auth` package (Actions installs requirements.txt).
    """
    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account
    except ImportError as e:
        raise RuntimeError(
            "queue transport needs google-auth + requests in an env with them "
            "installed (local: .venv per README; Actions: requirements.txt)") from e

    if service_account_info is None:
        load_dotenv()  # local dev fallback; Actions injects env vars directly
        info = json.loads(os.environ["GCP_SA_JSON"])
    else:
        info = service_account_info
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=[SHEETS_SCOPE])

    def transport(method, url, body):
        if not creds.valid:          # don't mint a fresh token per call
            creds.refresh(Request())
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Authorization": f"Bearer {creds.token}",
                     "Content-Type": "application/json"},
            method=method)
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)

    return transport


def read_tab(transport, sheet_id, tab):
    """All current values of a tab (list of rows), or [] when empty."""
    resp = transport("GET", f"{SHEETS_API_BASE}/{sheet_id}/values/{tab}", None)
    return resp.get("values", [])


def main(argv, transport_factory=None):
    """CLI: queue an extractions JSON into the Pending tab.

    python3 scripts/sheets_queue.py --extraction data/raw/extractions-Y.json

    Dedupe: rows already present in the tab (same name+address,
    case-insensitive) are skipped. Main is refused upstream by the rail
    in append_rows regardless of --tab.
    """
    import argparse
    from scripts.pipeline_extract import dedupe_against_existing

    ap = argparse.ArgumentParser(description="Queue extraction rows into the Sheet")
    ap.add_argument("--extraction", required=True)
    ap.add_argument("--tab", default="Pending")
    args = ap.parse_args(argv[1:])

    with open(args.extraction, encoding="utf-8") as f:
        rows = json.load(f).get("rows", [])
    if not rows:
        print("nothing to queue")
        return 0

    make = transport_factory or make_transport
    transport = make()
    sheet_id = os.environ["SHEET_ID"]
    existing = [
        {"name": r[SCHEMA.index("name")] if len(r) > SCHEMA.index("name") else "",
         "address": r[SCHEMA.index("address")] if len(r) > SCHEMA.index("address") else ""}
        for r in read_tab(transport, sheet_id, args.tab)[1:]  # skip header row
    ]
    kept, dupes = dedupe_against_existing(rows, existing)
    if kept:
        ordered = [[str(r.get(f, "")) for f in SCHEMA] for r in kept]
        append_rows(transport, sheet_id, args.tab, ordered)
    print(f"queued {len(kept)} rows to {args.tab} ({dupes} duplicates skipped)")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv))
