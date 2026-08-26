# Malaysia Data Center Map

A free, open-source, community-checked map showing where data centers are in Malaysia, and roughly how much power (MW) each one uses. Think of it as a DIY, Malaysia-only alternative to paid tools like Baxtel — smaller in scope, verifiable, and open.

**Live map:** https://farithadnan.github.io/malaysia-heatmap-datacenter/

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

- **GitHub is credential-free by policy.** This repo is public → it holds **zero** secrets/variables — see [`docs/adr-001-local-llm-stages.md`](docs/adr-001-local-llm-stages.md) for why this amends spec §16's "via GitHub Actions" wording and why it's reversible.
- **GitHub Actions = free discovery only.** The weekly CI runs tests + the read-only watch sweep (public sources, no secrets) and archives findings. Fetch/Extract/Queue are **not** here.
- **Everything credentialed or spending runs locally:** `bash scripts/run_pipeline.sh` (watch → fetch → extract → queue), scheduled via Task Scheduler/cron — see [`docs/local-automation.md`](docs/local-automation.md).
- **Writes stay boxed no matter where they run:** extraction queues into the Sheet's **Pending** tab only (a hard rail in code refuses Main), and the public map renders from Main alone — nothing unreviewed reaches users automatically.

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

- **Code:** [MIT](LICENSE)
- **Data:** [ODbL 1.0](LICENSE-DATA.md) — this project uses OpenStreetMap data (© OpenStreetMap contributors), so the dataset follows its share-alike terms. When reusing the data, credit: `Data © OpenStreetMap contributors (ODbL 1.0), Malaysia Data Center Map project`.

## Data sources & limitations (read before citing)

- Figures are **research data, not live telemetry.** Every power number is either `confirmed` (from an official source) or `estimated`, and every row carries its `capacity_source` — never present an estimate as a fact.
- Sources: OpenStreetMap (Overpass), free public directory listings, company/government press releases, automated news/RSS monitoring (pending-review). No paywalled or login-gated data is used, ever.
- **Update cadence:** the map refreshes when the dataset updates — currently periodic, at data-center-industry pace (facilities take years to build). `last_updated` per row shows freshness; the repo's commit history is the audit trail.
- Coordinates for some facilities await geocoding/verification — those stay `needs review` and are not shown as final.

## Suggest a fix

Spotted a wrong or outdated entry? Open a [GitHub Issue](../../issues) with the facility name and a source — see [`CONTRIBUTING.md`](CONTRIBUTING.md). Every report goes through human verification; nothing reaches the map unreviewed.

Input welcome: corrections, new facilities with sources, better code, better maps.
