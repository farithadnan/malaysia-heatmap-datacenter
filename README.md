# Malaysia Data Center Map

A free, open-source, community-checked map showing where data centers are in Malaysia, and roughly how much power (MW) each one uses. Think of it as a DIY, Malaysia-only alternative to paid tools like Baxtel — smaller in scope, verifiable, and open.

> Current status: **specification stage** — the project spec is finalized; implementation has not started.

## What's in this repo

| File | Description |
|------|-------------|
| [`spec.md`](spec.md) | The full project specification (16 sections): goals, scope, data model, sources, automation pipeline, tech stack, roadmap, and rules. **Start here.** |
| `malaysia-datacenter-map-spec.md.pdf` | Original spec document (PDF export). `spec.md` is the working, greppable version of the same content. |
| [`docs/milestones/`](docs/milestones/README.md) | Task tracking: 7 phase milestones, 24 issues with acceptance criteria, and the `phase/N-*` branch mapping. |

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
