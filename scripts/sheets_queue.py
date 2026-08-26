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
    return (f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
            f"/values/{quoted}:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS")


def append_rows(transport, sheet_id, tab, rows):
    """Append rows to `tab` of the sheet. Returns the API response dict."""
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
            "google-auth is required for real Sheets writes; it is installed "
            "in GitHub Actions via requirements.txt") from e

    if service_account_info is None:
        load_dotenv()  # local dev fallback; Actions injects env vars directly
        info = json.loads(os.environ["GCP_SA_JSON"])
    else:
        info = service_account_info
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=[SHEETS_SCOPE])

    def transport(method, url, body):
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
