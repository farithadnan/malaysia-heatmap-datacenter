# Setup: Google Sheets API credentials (Issue #13)

What the pipeline needs to write findings into the **Pending** tab automatically.
~15 minutes, all free. You only do this once.

## 1. Create the spreadsheet (Issue #1)

1. Go to [sheets.google.com](https://sheets.google.com) → **Blank** sheet, name it e.g. `malaysia-datacenter-map`
2. Rename `Sheet1` → **`Main`**, add a second tab named **`Pending`**
3. Put this header row (spec §5) in **both** tabs (row 1):

   ```
   name,operator,address,latitude,longitude,capacity_mw,capacity_type,capacity_source,status,connection_voltage,verification_status,last_updated,report_url
   ```
4. Import `data/pending.csv` from this repo into the **Pending** tab:
   **File → Import → Upload → Replace current sheet** (row 1 already matches)
5. Copy the **Sheet ID** from the URL — it's the long string between `/d/` and `/edit`

## 2. Create a Google Cloud service account

1. [console.cloud.google.com](https://console.cloud.google.com) → sign in with the same Google account
2. Top bar project picker → **New Project** (e.g. `malaysia-dc-map`) → Create
3. **APIs & Services → Library** → search "**Google Sheets API**" → **Enable**
4. **IAM & Admin → Service Accounts → Create Service Account**
   - Name: `datacenter-map-bot` → Create → skip the optional role/permission steps (it needs nothing project-wide) → Done
5. In the service account list, click it → **Keys → Add Key → Create new key → JSON** → a `.json` file downloads
6. Open that file: note `client_email` (looks like `datacenter-map-bot@<project>.iam.gserviceaccount.com`) — you'll share the Sheet with this address
7. **Share the Sheet**: in Google Sheets → **Share** → paste the `client_email` → **Editor** → Send

## 3. Configure credentials locally (.env)

1. Copy the template: `cp .env.example .env`
2. Fill in:
   - `SHEET_ID` — from step 1.5
   - `GCP_SA_JSON` — the **entire contents** of the downloaded key JSON, on **one single line** (it starts `{"type": "service_account", ...}`)
3. `.env` is gitignored (verified); never commit it

## 4. Configure credentials for GitHub Actions (needed when the queue goes live weekly)

Repo → **Settings → Secrets and variables → Actions → New repository secret**, one entry per key:

| Secret | Value |
|---|---|
| `SHEET_ID` | the Sheet ID |
| `GCP_SA_JSON` | the one-line key JSON |

## 5. Sanity check (once filled in)

Local runs need `google-auth` installed (Actions installs it from
`requirements.txt`; locally it goes to your user site):

```bash
python3 -m pip install --user --break-system-packages google-auth
```

Then:

```bash
python3 - <<'EOF'
import os
from scripts.sheets_queue import make_transport
t = make_transport()   # loads .env, mints a service-account token
sid = os.environ["SHEET_ID"]
resp = t("GET", f"https://sheets.googleapis.com/v4/spreadsheets/{sid}", None)
print("auth OK — sheet reachable:", resp["properties"]["title"])
print("tabs:", [s["properties"]["title"] for s in resp["sheets"]])
EOF
```

Expect your sheet's title and `['Main', 'Pending']`. Any 401/403/404 means: Sheets API not enabled (step 2.3), Sheet not shared with the service account (step 2.7), or Sheet ID wrong (step 1.5).

## What writes where (spec §8 rule)

Automation only ever appends to **Pending**. It never touches **Main**, and
the map only ever renders rows from Main (exported via `scripts/csv_to_geojson.py`).
