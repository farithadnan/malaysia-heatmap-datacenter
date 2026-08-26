# Milestone: Phase 1 — Research

**Branch:** `phase/1-research` · **Spec:** §6 (sources), §7 (workflow)
**Goal:** 20–30 confirmed Malaysian data centers collected into the project's source-of-truth spreadsheet.

---

## Issue 1.1 — Set up the source-of-truth spreadsheet

**Labels:** `phase-1`, `data` · **Milestone:** Phase 1 — Research

Create the single Google Sheet (spec §8: one file, two tabs) that will hold all project data.

- Tab **Main** — trusted, confirmed rows; only this tab is ever exported to the map
- Tab **Pending** — unverified findings (from automation later, manual candidates now)
- Column schema exactly as spec §5: `name, operator, address, latitude, longitude, capacity_mw, capacity_type, capacity_source, status, connection_voltage, verification_status, last_updated, report_url`

**Acceptance criteria:**
- [ ] One spreadsheet, two tabs (Main, Pending), schema matches spec §5 verbatim
- [ ] Sheet is backed up / exportable to CSV for the repo
- [ ] Nothing is written to Main without human approval (working rule documented)

## Issue 1.2 — Pull the OSM seed list via Overpass API

**Labels:** `phase-1`, `data` · **Milestone:** Phase 1 — Research

Use Overpass Turbo (no code) to query `telecom=data_center` inside Malaysia's borders (Peninsular + Sabah/Sarawak) and save results into the spreadsheet.

**Acceptance criteria:**
- [ ] Query executed in Overpass Turbo; results exported
- [ ] Every result becomes a Pending-tab row with at minimum: name (if tagged), latitude, longitude, capacity_source = "OpenStreetMap"
- [ ] Result count recorded in the issue for reference

## Issue 1.3 — Add directory-listed facilities missing from OSM

**Labels:** `phase-1`, `data` · **Milestone:** Phase 1 — Research

Browse free listings on public directories (e.g. datacentermap.com, datacenters.com) and add any facility not already in the list. **No paywalled or login-gated content** (spec §6 rule).

**Acceptance criteria:**
- [ ] Free listings reviewed; delta facilities added to Pending tab
- [ ] Each row has name, operator, rough address, and source noted
- [ ] Duplicates against the OSM pull flagged for merging (not blindly duplicated)

## Issue 1.4 — Reach 20–30 confirmed facilities

**Labels:** `phase-1`, `data` · **Milestone:** Phase 1 — Research

Verify and promote enough rows from Pending to Main to hit the Phase 1 target (20–30 confirmed facilities, spec §13).

**Acceptance criteria:**
- [ ] Main tab holds ≥20 rows with name, operator, location, and `capacity_source` recorded
- [ ] Every row's `capacity_type` is honestly set (`confirmed`/`estimated`)
- [ ] `last_updated` is set for every promoted row
