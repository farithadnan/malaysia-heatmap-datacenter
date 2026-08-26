# Milestone: Phase 3 — Fill in the rest

**Branch:** `phase/3-fill-in-the-rest` · **Spec:** §2 (v1 target), §7 (workflow steps 5–6)
**Goal:** Every remaining known facility added — 30–50 total — including estimated ones, clearly marked.

---

## Issue 3.1 — Complete the dataset to 30–50 facilities

**Labels:** `phase-3`, `data` · **Milestone:** Phase 3 — Fill in the rest

Close the gap to the v1 target. For facilities with no public MW figure, estimate via `connection_voltage` or satellite footprint and mark `capacity_type = "estimated"` (spec §7 step 5, §14 honesty rules).

**Acceptance criteria:**
- [ ] Main tab reaches 30–50 rows (spec §16 checklist item 1)
- [ ] Every row has latitude/longitude (checklist item 2)
- [ ] Every row has a power value labeled confirmed or estimated (checklist item 3)
- [ ] No estimate is presented as confirmed

## Issue 3.2 — Dedupe pass across sources

**Labels:** `phase-3`, `data` · **Milestone:** Phase 3 — Fill in the rest

The same facility often appears under slightly different names across OSM, directories, and news (spec §7 step 6). Merge into one row per real facility.

**Acceptance criteria:**
- [ ] Name-similarity pass done; duplicates merged, richest data retained per field
- [ ] Each merged row keeps all its capacity_source references
- [ ] GeoJSON export after dedupe renders the same point count as Main rows
