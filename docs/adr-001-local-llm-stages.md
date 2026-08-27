# ADR 001: LLM and credentialed pipeline stages run locally, not in GitHub Actions

**Status:** Accepted (owner decision, 2026-08-26)
**Context:** Public repo. The spec §8/§13/§16 suggests GitHub Actions for the scheduled pipeline.
GitHub holds zero secrets by policy ("if it leaks, strangers drain the LLM quota").
**Decision:** GitHub Actions retains only the secrets-free **watch** sweep (tests + RSS/pages, artifacts).
Fetch, LLM Extract, and Sheet Queue run locally via `scripts/run_pipeline.sh` + `~/.env`,
scheduled by the owner's machine (Windows Task Scheduler / cron — see docs/local-automation.md).
**Consequences:**
- (+) No credential/endpoint URL of any kind exists on GitHub; public-repo leak blast radius = zero.
- (+) LLM usage stays on owner infrastructure (Modal endpoint) — data never leaves owner control.
- (−) Spec §16 wording ("pipeline running via GitHub Actions") is met only partially; this ADR
  records the intentional deviation. Weekly cadence is preserved by the local scheduler.
- (−) Pipeline pauses when the owner's machine is off; runs use "catch-up on miss" scheduling
  or manual `bash scripts/run_pipeline.sh`. Monthly-scale data makes this harmless (§15).
**Reversibility:** If a dedicated always-on runner appears, the same four CLIs run unchanged
via cron on it. Re-enabling GH Actions for credentialed stages is always possible with repo
secrets — but requires owner sign-off and this ADR's revision.
