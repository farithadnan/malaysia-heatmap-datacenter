# Milestone: Phase 4 — Automate the search

**Branch:** `phase/4-automate-the-search` · **Spec:** §8 (the entire pipeline)
**Goal:** The four-stage pipeline — Watch, Fetch, Extract, Queue — running weekly via GitHub Actions, writing only to the Pending tab.

---

## Issue 4.1 — Watch: standing RSS queries + source page monitors

**Labels:** `phase-4`, `pipeline` · **Milestone:** Phase 4 — Automate the search

Set up free Google News RSS feeds for `data center Malaysia MW`, `MIDA data centre`, `TNB data centre`; check whether MIDA/TNB newsroom pages have RSS, else implement page-snapshot diffing.

**Acceptance criteria:**
- [ ] RSS feed URLs documented in the repo
- [ ] For non-RSS sources, a snapshot-and-diff mechanism flags new content
- [ ] Only public/no-login sources are watched (spec §8 legality table)

## Issue 4.2 — Fetch: scheduled downloader

**Labels:** `phase-4`, `pipeline` · **Milestone:** Phase 4 — Automate the search

Python script (`requests`, `feedparser`) that downloads full text of new articles found by Watch; downloads Bank Negara's newest Quarterly Bulletin PDF when published (~quarterly).

**Acceptance criteria:**
- [ ] Script fetches and stores latest items idempotently (re-runs don't duplicate)
- [ ] BNM PDF path implemented separately from article text path
- [ ] Errors logged without aborting the whole run

## Issue 4.3 — Extract: LLM structured-facts step

**Labels:** `phase-4`, `pipeline` · **Milestone:** Phase 4 — Automate the search

Feed fetched text to an LLM API (Claude) with the spec §8 prompt shape: return name/operator/location/MW as structured data, or nothing if absent.

**Acceptance criteria:**
- [ ] Output validates against the spec §5 data model before queuing
- [ ] Extractions include the source URL and extraction date
- [ ] Texts with no relevant facts produce no rows

## Issue 4.4 — Queue: Sheets API writer (Pending tab only)

**Labels:** `phase-4`, `pipeline` · **Milestone:** Phase 4 — Automate the search

Write each extraction as a new row in the **Pending** tab via the Google Sheets API. Never writes to Main; never touches the map (spec §8).

**Acceptance criteria:**
- [ ] Credentials via environment/secrets, never committed (`.gitignore` already covers)
- [ ] New rows include `verification_status = "needs review"`
- [ ] Manual test: run → row appears in Pending, Main untouched

## Issue 4.5 — GitHub Actions scheduled workflow

**Labels:** `phase-4`, `pipeline` · **Milestone:** Phase 4 — Automate the search

Free scheduled workflow running the fetch+extract+queue script weekly (configurable to monthly), no server needed.

**Acceptance criteria:**
- [ ] Workflow file in `.github/workflows/` with cron schedule
- [ ] Secrets configured in repo settings (not in yaml)
- [ ] Successful scheduled run demonstrated (spec §16 checklist item 7)

## Issue 4.6 — Bank Negara national-total cross-check

**Labels:** `phase-4`, `pipeline` · **Milestone:** Phase 4 — Automate the search

After each BNM extraction, auto-sum the Main tab's `capacity_mw` and compare against the national figure (~784 MW late 2025); print a warning on large divergence (spec §8).

**Acceptance criteria:**
- [ ] Comparison runs as part of the pipeline
- [ ] Warning threshold documented and triggered correctly in a test case
- [ ] Result logged in the Actions run output
