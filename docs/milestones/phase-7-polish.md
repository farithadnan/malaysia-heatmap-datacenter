# Milestone: Phase 7 — Polish

**Branch:** `phase/7-polish` · **Spec:** §13 (phase 7), §2, §16
**Goal:** Legend, status color-coding, search/filter — then deploy with a shareable link.

---

## Issue 7.1 — Legend + status color-coding

**Labels:** `phase-7`, `ux`, `map` · **Milestone:** Phase 7 — Polish

Add a legend explaining marker size (MW) and color-code markers by status: operating / under construction / planned (spec §13). Keep the confirmed-vs-estimated distinction from Phase 2 visible.

**Acceptance criteria:**
- [ ] Legend visible on the map
- [ ] Status colors applied and documented in the legend
- [ ] Map remains readable on mobile-width screens

## Issue 7.2 — Search / filter box

**Labels:** `phase-7`, `ux`, `map` · **Milestone:** Phase 7 — Polish

Let visitors filter or search facilities (e.g. by name, state, status, minimum MW — spec §9's example filter: "show me sites over 50 MW in Johor").

**Acceptance criteria:**
- [ ] Search by facility name/operator
- [ ] At least one structured filter (status or MW threshold)
- [ ] Filtering does not require a page reload

## Issue 7.3 — Deploy publicly

**Labels:** `phase-7`, `meta` · **Milestone:** Phase 7 — Polish

Deploy the static site to GitHub Pages (or Netlify/Vercel) and wire the shareable link into the README (spec §16 checklist item 6).

**Acceptance criteria:**
- [ ] Public URL serves the current map + dataset
- [ ] README links the live map
- [ ] Final pass over spec §16 success checklist — all 11 items checked
