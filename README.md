# Malaysia Data Center Map

A free, open-source, community-checked map showing where data centers are in Malaysia, and roughly how much power (MW) each one uses. Think of it as a DIY, Malaysia-only alternative to paid tools like Baxtel — smaller in scope, verifiable, and open.

> Current status: **early build** — static map live, the four pipeline stages (Watch/Fetch/Extract/Queue) are implemented and individually verified; full end-to-end automation is the active work.

## What's in this repo

| File | Description |
|------|-------------|
| [`spec.md`](spec.md) | The full project specification (16 sections): goals, scope, data model, sources, automation pipeline, tech stack, roadmap, and rules. **Start here.** |
| `malaysia-datacenter-map-spec.md.pdf` | Original spec document (PDF export). `spec.md` is the working, greppable version of the same content. |
| [`docs/milestones/`](docs/milestones/README.md) | Task tracking: 7 phase milestones, 24 issues with acceptance criteria, and the `phase/N-*` branch mapping. |
| [`docs/setup-google-sheets-api.md`](docs/setup-google-sheets-api.md) | Step-by-step: spreadsheet creation, service account, `.env` & GitHub secrets setup for the automation pipeline. |
| `index.html` | The Leaflet map (Phase 2). Serve the repo root over HTTP and open it: `python3 -m http.server`. |
| `data/` | Dataset: `main.csv` (approved rows), `pending.csv` (review queue), `datacenters.geojson` (map export), `queries/`, `raw/`. |
| `scripts/csv_to_geojson.py` | Spreadsheet → GeoJSON converter. Stdlib only: `python3 -m scripts/csv_to_geojson.py data/main.csv data/datacenters.geojson`. |
| `scripts/pipeline_watch.py` | Watch stage (spec §8): Google News RSS + MIDA/TNB page snapshots. `python3 -m scripts/pipeline_watch.py --config data/sources.json --out <findings.json> --state data/raw/page-state.json` |
| `scripts/pipeline_fetch.py` | Fetch stage: idempotent article/PDF downloader. `python3 -m scripts/pipeline_fetch.py --findings <findings.json> --state data/raw/download-state.json --articles data/raw/articles` |
| `scripts/sheets_queue.py` | Queue stage: appends validated rows to the Sheet's **Pending** tab (hard rail: never Main). Needs `GCP_SA_JSON` + Sheet ID in Actions secrets. |
| `scripts/llm/` | LLM provider layer: declarative registry (`providers.py`), wire dialects (`clients.py`), tolerant JSON parsing (`parsing.py`). Env-driven: Anthropic/DeepSeek/OpenAI-compatible (Modal, Fireworks…). |
| `scripts/common.py` | Single home for shared pipeline primitives (browser UA, link→filename digest contract). |
| `scripts/pipeline_extract.py` | Extract stage: LLM pulls name/operator/location/MW from article text. Provider-generic: Anthropic, DeepSeek, any OpenAI-compatible endpoint (Modal, Groq…); optional Firecrawl scraping. Env keys in `.env.example`. |
| `tests/` | Unit tests (stdlib `unittest`): `python3 -m unittest discover -s tests`. |

## Local setup

```bash
python3 -m pip install --user --break-system-packages virtualenv  # one time (no python3.12-venv on this box)
python3 -m virtualenv .venv
.venv/bin/pip install -r requirements.txt
```

Rules: tests run on plain `python3` (stdlib-only, no deps); anything that talks to
external services uses `.venv/bin/python`; credentials live in `.env` (copy
`.env.example`, see [`docs/setup-google-sheets-api.md`](docs/setup-google-sheets-api.md)).
The map itself needs no setup: `python3 -m http.server` and open the browser.

## Automation safety model

- **Weekly cron = read-only.** Watch sweep + tests. No LLM spend, no Sheet writes, no map changes — ever.
- **The switch:** repo Settings → Secrets and variables → Variables → `PIPELINE_LLM_ENABLED`. Anything that costs money (LLM calls) or writes data (Sheet queue) runs only when this is `true`. Default: `false`.
- **Even when ON, writes are boxed:** extraction queues into the Sheet's **Pending** tab only (a hard rail in code refuses Main), and the public map renders from Main only — nothing unreviewed ever reaches users automatically.
- **The AI stays in your infrastructure:** with your current `.env`, extraction calls go to your own Modal endpoint. Data leaves your hands only if you point `LLM_*` at an external vendor.

## What will be built (per the spec)

- **Static map** — Leaflet.js + OpenStreetMap/CARTO tiles, one marker per data center, marker size/color = MW, hosted free on GitHub Pages/Netlify/Vercel.
- **Open dataset** — a spreadsheet (Google Sheets → GeoJSON) with 13 fields per facility: location, operator, capacity (confirmed/estimated), status, sources, and freshness.
- **Automation pipeline** — Watch → Fetch → Extract → Queue: Google News RSS + MIDA/TNB/Bank Negara sources fetched by Python, facts extracted via an LLM API, findings queued in a Pending tab for human review before ever reaching the map.
- **Community corrections** — pre-filled "Report an issue" links on each marker + a Google Form, both routed into the same review queue.

Core rules: free public sources only, every number cites its source, estimates are labeled estimates, OSM gets attribution, and a human approves everything before it goes live.

## Roadmap (spec §13)

1. Research — seed 20–30 confirmed facilities (Overpass/OSM + directories)
2. Static map — basic Leaflet map reading a GeoJSON export
3. Fill in the rest — complete 30–50 facilities, estimates clearly marked
4. Automate — four-stage pipeline on GitHub Actions (weekly)
5. Open source — public repo, license (MIT code / ODbL-checked data), README
6. Community feedback — report links wired into the review queue
7. Polish — legend, status colors, search/filter, deploy

## License

Not yet decided — see spec §11 (MIT for code, ODbL compatibility check required for OSM-derived data).
