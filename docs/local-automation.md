# Local automation (the trusted zone)

Security model (owner decision, 2026-08-26):

| Zone | Runs | Holds credentials? |
|---|---|---|
| **GitHub** (public repo) | Static map hosting, issues/milestones, free **read-only** watch CI | **None — zero secrets/variables** |
| **Your machine** (`.env`) | Everything credentialed or spending: Fetch, LLM Extract, Sheet Queue | `.env` only, gitignored |

Anything involving LLM keys, endpoint URLs, Google/Sheet credentials, or money
must never go into GitHub Actions/secrets/variables — the repo is public.
A leaked credential on a public repo = strangers draining your LLM quota.

## One pipeline pass locally

```bash
bash scripts/run_pipeline.sh
```

Sequenced: watch → fetch → extract → queue, date-stamped outputs in `data/raw/`.
Safe to re-run: fetch and queue both dedupe — re-runs cost nothing but the LLM
calls on genuinely new-ish text (dedupe happens BEFORE queueing, after
extraction, and LLM only reads articles fetch has never seen).

### Credential-free dry run (no `.env` needed)

To exercise only the read-only stages — **watch** and **fetch** — and skip the
LLM extract + Sheets queue stages (which need `.env` credentials), pass the flag:

```bash
bash scripts/run_pipeline.sh --no-credentials
```

This is useful before you have your LLM/Sheets keys, or to re-run just the
discovery half of the pipeline without spending any LLM calls.

## Scheduling it (pick one)

### Windows Task Scheduler (recommended on this box)

No Docker/WSL-cron quirks: the task fires even if WSL isn't already running.

```
Program:  wsl.exe
Arguments: -e bash -lc "cd /mnt/f/dev/malaysia-heatmap-datacenter && bash scripts/run_pipeline.sh >> data/raw/pipeline.log 2>&1"
Trigger:  Weekly, e.g. Monday 09:00
Settings: "Run only when user is logged on" is fine (your machine makes the calls);
          enable "Run task as soon as possible after a scheduled start is missed"
```

### WSL cron (if the distro stays running)

```cron
0 9 * * 1  cd /mnt/f/dev/malaysia-heatmap-datacenter && bash scripts/run_pipeline.sh >> data/raw/pipeline.log 2>&1
```

### Docker (optional, only if you want isolation)

A plain `python:3.12-slim` image mounting the repo + `.env` works, but adds
build/pull overhead for what is currently a bash script. Skip it unless the
need appears (e.g. moving the runner to a small always-on box/VPS).

## What you get

- `data/raw/pipeline.log` — full run log (when scheduled)
- `data/raw/watch-YYYY-MM-DD.json` — what sources produced
- `data/raw/extractions-YYYY-MM-DD.json` — what the LLM pulled out (+ skip reasons)
- New rows appear in your Sheet's **Pending** tab only; the public map is
  untouched until you promote rows to Main yourself.
