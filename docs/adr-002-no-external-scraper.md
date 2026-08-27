# ADR 002: No external scraping service — local text extraction only

**Status:** Accepted (owner decision, 2026-08-27)
**Context:** During setup the owner meant to use **Fireworks.ai** as the LLM extraction
provider but accidentally wired in **Firecrawl** (a third-party scraping SaaS) as an
"optional article scraper" for JS-heavy news pages, including a separate `FC_API_KEY`.
The spec's scraping requirement (§8 stage 2 "Fetch") is met by a plain script that
downloads a public page and compares it to last time — not by any external scraper.
All verified pipeline sources (spec §8: Equinix PDFs, MIDA releases, TNB press pages,
Google News RSS) are direct-download HTML/PDF with no JS-rendering requirement.
**Decision:** Remove Firecrawl entirely. No `FC_API_KEY`, no `make_firecrawl_scraper`,
no scraper param in the Extract stage. Article text is stripped locally with the
stdlib HTML parser (`html_to_text` in `scripts/pipeline_extract.py`).
**Consequences:**
- (+) One fewer third-party dependency, API key, network call, and failure mode (rate
  limits, billing, outages). No per-scrape cost.
- (+) Matches the spec exactly — spec's "scrape" needs are covered by Fetch + local stripper.
- (−) If a genuinely JS-rendered article is encountered later, plain HTML fetch yields
  boilerplate instead of article body; a scraper would need to be re-added at that point.
**Reversibility:** Cheap to re-add. The Extract stage's `run_extraction` seam (a `scraper`
callable: `url -> text`) can be reintroduced behind a new opt-in env key without touching
the LLM/provider layer. Revisit only when a real pipeline run hits a JS-only source.
