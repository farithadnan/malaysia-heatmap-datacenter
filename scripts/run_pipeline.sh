#!/usr/bin/env bash
# Local pipeline runner — ONE pass through all four stages, on YOUR machine.
# Everything that touches credentials, money (LLM), or writes data runs HERE
# only. GitHub holds zero secrets (security decision, 2026-08-26).
#
# Usage:  bash scripts/run_pipeline.sh [--no-credentials]
#   --no-credentials : run only the read-only stages (watch, fetch) and skip the
#                      LLM extract + Sheets queue stages, which need .env credentials.
#   Cron: see docs/local-automation.md
set -euo pipefail
cd "$(dirname "$0")/.."

NO_CREDS=0
[ "${1:-}" = "--no-credentials" ] && NO_CREDS=1

TODAY=$(date +%F)
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3   # watch/fetch are stdlib; extract needs venv only for queue's google-auth

echo "== 1/4 watch (read-only sources) =="
$PY -m scripts.pipeline_watch --config data/sources.json \
    --out "data/raw/watch-$TODAY.json" --state data/raw/page-state.json

echo "== 2/4 fetch (new items only) =="
$PY -m scripts.pipeline_fetch --findings "data/raw/watch-$TODAY.json" \
    --state data/raw/download-state.json --articles data/raw/articles

if [ "$NO_CREDS" -eq 1 ]; then
  echo "== 3/4 SKIPPED (extract needs LLM credentials in .env) =="
  echo "== 4/4 SKIPPED (queue needs GCP_SA_JSON + SHEET_ID in .env) =="
  echo "== done (read-only only): $(date -Is) =="
  exit 0
fi

echo "== 3/4 extract (LLM — your endpoint, .env) =="
# Modal-style serverless endpoints can answer 401/503 while cold-starting;
# retry the whole stage a few times before failing the run.
for attempt in 1 2 3; do
  if $PY -m scripts.pipeline_extract --articles data/raw/articles \
      --findings "data/raw/watch-$TODAY.json" \
      --out "data/raw/extractions-$TODAY.json" \
      --existing data/main.csv data/pending.csv; then
    break
  fi
  echo "extract attempt $attempt failed; waiting 45s for endpoint warmup..."
  sleep 45
done

echo "== 4/4 queue (Pending tab only; Main is code-railed) =="
$PY -m scripts.sheets_queue --extraction "data/raw/extractions-$TODAY.json"

echo "== done: $(date -Is) =="
