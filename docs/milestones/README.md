# Milestones & Issues

Task tracking for the 7 build phases from [spec §13](../spec.md#13-build-phases-suggested-roadmap).

Each phase = one milestone + one long-lived branch (`phase/N-slug`) + a set of issues.
Work happens on the phase branch and merges to `main` via PR when the phase's acceptance criteria pass.

## Index

| # | Milestone | Branch | Issues | Spec |
|---|-----------|--------|--------|------|
| 1 | Research | `phase/1-research` | 4 | §6, §7 |
| 2 | Static map | `phase/2-static-map` | 3 | §2, §9 |
| 3 | Fill in the rest | `phase/3-fill-in-the-rest` | 2 | §2, §7 |
| 4 | Automate the search | `phase/4-automate-the-search` | 6 | §8 |
| 5 | Go open source | `phase/5-go-open-source` | 3 | §11 |
| 6 | Community feedback | `phase/6-community-feedback` | 3 | §12 |
| 7 | Polish | `phase/7-polish` | 3 | §13 |

**Total: 24 issues.**

## Issue file format

Each issue entry is ready to post to GitHub verbatim:

- **Title** — the issue title
- **Labels** — `phase-N` + a domain label (`data`, `map`, `pipeline`, `community`, `meta`, `ux`, `docs`, `legal`)
- **Milestone** — the phase it belongs to
- **Body / Acceptance criteria** — what must be true to close it

## Publishing these to GitHub (one-time)

Requires the GitHub CLI (not currently installed) and a GitHub remote:

```bash
# 1. Install gh: https://cli.github.com/ — then:
gh auth login
# 2. Create the remote repo and push:
gh repo create malaysia-heatmap-datacenter --public --source=. --push
# 3. Milestones (one per phase), e.g.:
gh api repos/:owner/:repo/milestones -f title="Phase 1 — Research"
# 4. Issues, e.g. from these files:
gh issue create --title "..." --milestone "Phase 1 — Research" --label "phase-1,data" --body-file <file>
```

Once `gh` is available, this step can be automated with a small script iterating over these files.
Until then, this directory is the source of truth for task tracking.
