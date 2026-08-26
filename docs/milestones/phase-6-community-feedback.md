# Milestone: Phase 6 — Community feedback

**Branch:** `phase/6-community-feedback` · **Spec:** §12
**Goal:** A lightweight way for anyone to flag wrong/outdated entries, routed into the same Pending tab as the automation.

---

## Issue 6.1 — Pre-filled "Report an issue" links on map popups

**Labels:** `phase-6`, `community`, `map` · **Milestone:** Phase 6 — Community feedback

Each marker popup gets a link that opens a new GitHub issue pre-filled with that facility's name, so reporters only describe what's wrong (spec §12).

**Acceptance criteria:**
- [ ] Every popup includes a working report link (spec §16 checklist item 10)
- [ ] Pre-filled content includes facility name and current values
- [ ] Link opens correctly for logged-in GitHub users

## Issue 6.2 — GitHub issue template for corrections

**Labels:** `phase-6`, `community` · **Milestone:** Phase 6 — Community feedback

An issue template for data corrections: which facility, which field, what's wrong, source for the correction.

**Acceptance criteria:**
- [ ] `.github/ISSUE_TEMPLATE/` contains the correction template
- [ ] Template asks for a verifiable source (spec §14: verify before confirming)

## Issue 6.3 — Google Form alternative + routing to Pending tab

**Labels:** `phase-6`, `community` · **Milestone:** Phase 6 — Community feedback

Free Google Form ("See something wrong? Tell us here") for non-GitHub users, feeding a "reported corrections" area. All reports — GitHub or form — land in the single Pending tab with `verification_status` / `report_url` updated (spec §12).

**Acceptance criteria:**
- [ ] Form linked from each popup alongside the GitHub link
- [ ] Both report channels converge on the Pending tab
- [ ] Confirmed corrections set `verification_status = "confirmed"` + source noted
