# Milestone: Phase 5 — Go open source

**Branch:** `phase/5-go-open-source` · **Spec:** §11
**Goal:** Repo published publicly with correct licensing, a trustworthy README, and PRs enabled.

---

## Issue 5.1 — Add licenses (code + data)

**Labels:** `phase-5`, `legal` · **Milestone:** Phase 5 — Go open source

Add MIT license for code. For data, review ODbL compatibility first — the dataset includes OpenStreetMap-derived data, and ODbL requires attribution and in some cases share-alike (spec §11). Read OSM's license summary before publishing.

**Acceptance criteria:**
- [ ] `LICENSE` (MIT) added for code
- [ ] ODbL review documented; data license added or decision recorded
- [ ] OSM attribution present in README and on the map (already required by Phase 2)

## Issue 5.2 — README ready for the public

**Labels:** `phase-5`, `docs` · **Milestone:** Phase 5 — Go open source

Extend the existing README: what the project is, where data comes from, how often it updates, how to suggest a fix (spec §11: "this is what turns a personal project into something others can trust and contribute to"). Include the spec §16 "sources and limitations" note for the site.

**Acceptance criteria:**
- [ ] README covers: purpose, data sources, update cadence, how-to-fix
- [ ] Data-sources-and-limitations note exists (spec §16 checklist item 11)

## Issue 5.3 — Publish: public repo + contribution flow

**Labels:** `phase-5`, `meta` · **Milestone:** Phase 5 — Go open source

Make the GitHub repo public; enable and document the pull-request flow so technical users can propose exact row changes for approval (spec §11).

**Acceptance criteria:**
- [ ] Repo public; milestone issues from `docs/milestones/` posted to GitHub
- [ ] CONTRIBUTING note or PR template in place
- [ ] spec §16 checklist item 9 satisfied
