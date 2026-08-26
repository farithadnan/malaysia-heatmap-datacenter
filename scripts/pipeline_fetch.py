"""Fetch stage of the data-collection pipeline (spec §8, stage 2).

Downloads the content of articles found by the Watch stage. Idempotent:
the state file remembers every downloaded link, so re-runs only fetch
genuinely new items. PDFs (e.g. Bank Negara Quarterly Bulletins) are
kept as-is; everything else is saved as HTML. Errors are recorded, never
fatal (Issue #11 acceptance). Output layout: <articles_dir>/<date>/<digest>.<ext>
where digest = scripts.common.link_digest(link) — Extract reads the same root
recursively; the naming contract is shared, not copied.

CLI:
    python3 scripts/pipeline_fetch.py --findings data/raw/watch-2026-08-26.json \
        --state data/raw/download-state.json --articles data/raw/articles
"""
import argparse
import json
import os
import urllib.request
from datetime import date

from scripts.common import USER_AGENT, link_digest

MAX_BYTES = 20 * 1024 * 1024  # sanity cap for PDFs / pages


def is_pdf(content):
    return content[:5] == b"%PDF-"


def plan_downloads(findings, state):
    """Articles not yet in the downloaded state set."""
    return [a for a in findings.get("articles", []) if a.get("link") and a["link"] not in state]


def download(url, fetcher):
    try:
        return fetcher(url), None
    except Exception as e:
        return None, f"{url}: {e}"


def fetch_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=45) as r:
        if r.length and r.length > MAX_BYTES:
            raise ValueError(f"response too large ({r.length} bytes)")
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:   # declared or not: over limit is over limit
        raise ValueError(f"response too large (>{MAX_BYTES} bytes)")
    return data


def run(findings_path, state_path, articles_dir, today=None, fetcher=fetch_bytes):
    today = today or date.today().isoformat()
    with open(findings_path, encoding="utf-8") as f:
        findings = json.load(f)
    try:
        with open(state_path, encoding="utf-8") as f:
            state = set(json.load(f).get("downloaded", []))
    except (OSError, json.JSONDecodeError):
        state = set()

    plan = plan_downloads(findings, state)
    day_dir = os.path.join(articles_dir, today)
    errors = []
    downloaded = 0
    for article in plan:
        content, err = download(article["link"], fetcher)
        if err:
            errors.append(err)
            continue
        ext = ".pdf" if is_pdf(content) else ".html"
        os.makedirs(day_dir, exist_ok=True)
        digest = link_digest(article["link"])
        with open(os.path.join(day_dir, digest + ext), "wb") as f:
            f.write(content)
        state.add(article["link"])
        downloaded += 1

    state_dir = os.path.dirname(state_path)
    if state_dir:
        os.makedirs(state_dir, exist_ok=True)
    with open(state_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"downloaded": sorted(state)}, f, indent=2)
        f.write("\n")

    return {
        "date": today,
        "planned": len(plan),
        "downloaded": downloaded,
        "skipped_seen": len(findings.get("articles", [])) - len(plan),
        "errors": len(errors),
        "error_details": errors,
    }


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--findings", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--articles", required=True)
    args = ap.parse_args(argv[1:])
    report = run(args.findings, args.state, args.articles)
    for e in report["error_details"]:
        print(f"warning: {e}")
    print(f"fetch {report['date']}: {report['downloaded']} downloaded, "
          f"{report['skipped_seen']} already seen, {report['errors']} errors")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv))
