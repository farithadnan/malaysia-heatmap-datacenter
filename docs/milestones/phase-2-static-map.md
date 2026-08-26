# Milestone: Phase 2 — Static map

**Branch:** `phase/2-static-map` · **Spec:** §2 (done-criteria), §9 (tech stack), §10 (manual + map flow)
**Goal:** A basic Leaflet map that plots the spreadsheet's points from a GeoJSON file, with a popup showing name and MW on click.

---

## Issue 2.1 — Spreadsheet/CSV → GeoJSON export script

**Labels:** `phase-2`, `data` · **Milestone:** Phase 2 — Static map

A small script that converts the Main tab's export (CSV) into a `datacenters.geojson` file the map can read. Storage stays decoupled from the frontend (spec §9), so the script is the single conversion point.

**Acceptance criteria:**
- [ ] Script regenerates GeoJSON deterministically from a CSV export
- [ ] All 13 data-model fields carried through into GeoJSON properties
- [ ] Rows missing coordinates are skipped with a warning, not silently dropped

## Issue 2.2 — Basic Leaflet map page

**Labels:** `phase-2`, `map` · **Milestone:** Phase 2 — Static map

A single static page: Leaflet.js + free tiles (OpenStreetMap or CARTO), reading the GeoJSON file, one marker per facility. Marker size or color encodes `capacity_mw` (spec §9).

**Acceptance criteria:**
- [ ] Page opens locally in a browser with no build step
- [ ] All GeoJSON points plotted; map centered/fitted on Malaysia
- [ ] OpenStreetMap attribution visible on the map (spec §14 — license condition, not optional)

## Issue 2.3 — Marker popup with details

**Labels:** `phase-2`, `map` · **Milestone:** Phase 2 — Static map

Clicking a marker shows the facility's details.

**Acceptance criteria:**
- [ ] Popup shows: name, operator, capacity_mw with `capacity_type` label, status, and capacity_source
- [ ] Estimated capacities are visually/verbally distinguishable from confirmed ones
