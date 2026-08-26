"""Extract stage (spec §8, stage 3): pull structured data-center facts out of
article text with an LLM.

Extraction-domain logic lives HERE (prompt wording, §5 schema validation,
provenance, dedupe, scraping). LLM *provider* logic lives in scripts/llm/:
- providers.py  — declarative registry of all providers + aliases
- clients.py    — the two API dialects (Anthropic messages / OpenAI chat)
- parsing.py    — tolerant JSON-object extraction

Provider config is env-driven (.env / secrets); no provider is hardcoded
into control flow anywhere.

Every fact row carries its source URL + extraction date (spec); rows failing
the spec §5 schema are dropped with a reason; texts with no relevant facts
produce nothing.
"""
import argparse
import csv
import glob
import json
import os
import re
from datetime import date
from html.parser import HTMLParser

from scripts.common import link_digest
from scripts.csv_to_geojson import SCHEMA
from scripts.env import load_dotenv
from scripts.llm import make_llm_client_from_env  # provider factory (scripts/llm)
from scripts.llm.clients import post_json

FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v1/scrape"
MAX_ARTICLE_CHARS = 12_000          # keep prompts cheap; big articles truncate
STATUS_VALUES = {"", "operating", "under construction", "planned"}
CAPACITY_TYPES = {"", "confirmed", "estimated"}

# ---------------------------------------------------------------- scraping --

class _TextStripper(HTMLParser):
    SKIP = {"script", "style", "noscript", "head"}

    def __init__(self):
        super().__init__()
        self.parts, self._skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def html_to_text(html):
    p = _TextStripper()
    p.feed(html)
    return " ".join("".join(p.parts).split())


def make_firecrawl_scraper(api_key, poster=post_json):
    """Firecrawl /scrape as a scraper: url -> clean markdown text (None on fail)."""
    def scrape(url):
        resp = poster(FIRECRAWL_SCRAPE_URL,
                      {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                      {"url": url, "formats": ["markdown"]})
        if not resp.get("success"):
            return None
        return resp.get("data", {}).get("markdown")
    return scrape

# ------------------------------------------------------------- llm clients --

def build_prompt(article_text):
    return ("""You extract data-center facts from news text for a Malaysian data-center tracker.

RULES:
- Only extract if the text mentions a data center in MALAYSIA (Peninsular or Sabah/Sarawak).
- Pull out: name, operator, address/location ("location" field), power capacity in MW,
- If the text has no such facts, return nothing: {"found": false}.
- Otherwise reply with ONE JSON object, no prose:
{"found": true, "name": "...", "operator": "...", "location": "...", "capacity_mw": <number or null>, "capacity_type": "confirmed|estimated", "status": "operating|under construction|planned"}

ARTICLE:
""" + article_text[:MAX_ARTICLE_CHARS])



# ------------------------------------------------------------- orchestration --

def validate_extraction(d):
    """Against the spec §5 data model. Returns (ok, reasons[])."""
    errors = []
    if not str(d.get("name") or "").strip():
        errors.append("missing/blank name")
    mw = d.get("capacity_mw")
    if mw not in (None, ""):
        try:
            float(str(mw).replace("MW", "").strip())
        except (TypeError, ValueError):
            errors.append(f"capacity_mw not numeric: {mw!r}")
    ctype = str(d.get("capacity_type") or "").strip()
    if ctype not in CAPACITY_TYPES:
        errors.append(f"bad capacity_type: {ctype!r}")
    status = str(d.get("status") or "").strip()
    if status not in STATUS_VALUES:
        errors.append(f"bad status: {status!r}")
    return (not errors, errors)


def extract_article(article_text, source_url, llm_client, today):
    """One article -> (row | None, reason). Schema rows only, with provenance."""
    if not article_text or not article_text.strip():
        return None, "empty article"
    parsed = llm_client(build_prompt(article_text))
    if not isinstance(parsed, dict):
        return None, "model returned no JSON"
    if not parsed.get("found"):
        return None, "no facts found"
    ok, reasons = validate_extraction(parsed)
    if not ok:
        return None, "; ".join(reasons)
    row = {field: "" for field in SCHEMA}
    row.update({
        "name": str(parsed.get("name", "")).strip(),
        "operator": str(parsed.get("operator", "") or "").strip(),
        "address": str(parsed.get("location", parsed.get("address", "")) or "").strip(),
        "capacity_mw": re.sub(r"(?i)\s*mw\s*$", "", str(parsed.get("capacity_mw") or "")).strip(),
        "capacity_type": str(parsed.get("capacity_type") or "estimated").strip(),
        "capacity_source": f"article: {source_url}",
        "status": str(parsed.get("status") or "").strip(),
        "verification_status": "needs review",
        "last_updated": today,
        "report_url": source_url,
    })
    return row, None


def dedupe_against_existing(new_rows, existing_rows):
    """Skip rows whose (name, address) already exists. Case/space-insensitive."""
    def key(r):
        return (re.sub(r"\s+", " ", r.get("name", "")).strip().lower(),
                re.sub(r"\s+", " ", r.get("address", "")).strip().lower())
    seen = {key(r) for r in existing_rows}
    kept, skipped = [], 0
    for r in new_rows:
        if key(r) in seen:
            skipped += 1
        else:
            kept.append(r)
            seen.add(key(r))
    return kept, skipped


def run_extraction(articles_dir, findings_path, llm_client, today, scraper=None):
    """All .html/.md articles from a watch/fetch sweep -> schema rows + skip log."""
    with open(findings_path, encoding="utf-8") as f:
        findings = json.load(f)
    by_digest = {}
    for a in findings.get("articles", []):
        by_digest[link_digest(a["link"])] = a

    patterns = ["**/*.html", "**/*.md", "*.html", "*.md"]
    paths = sorted({p for pat in patterns
                    for p in glob.glob(os.path.join(articles_dir, pat), recursive=True)})
    rows, skipped = [], []
    for path in paths:
        digest = os.path.splitext(os.path.basename(path))[0]
        article = by_digest.get(digest)
        link = article["link"] if article else None
        source = link or f"{articles_dir}/{digest}"
        if scraper and link:
            try:
                text = scraper(link)
            except Exception:      # scraper down/bad key -> local stripper is the seam
                text = None
            if text is None:
                with open(path, encoding="utf-8", errors="replace") as f:
                    text = html_to_text(f.read())
        else:
            with open(path, encoding="utf-8", errors="replace") as f:
                text = html_to_text(f.read())
        row, reason = extract_article(text, source, llm_client, today)
        if row:
            rows.append(row)
        else:
            skipped.append({"digest": digest, "reason": reason})
    return {"date": today, "rows": rows, "skipped": skipped}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--articles", required=True, help="dir of fetched article files")
    ap.add_argument("--findings", required=True, help="watch findings JSON (for URLs)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--existing", nargs="*", default=[], help="CSV files to dedupe against")
    args = ap.parse_args(argv[1:])

    load_dotenv()
    client = make_llm_client_from_env(os.environ)
    scraper = (make_firecrawl_scraper(os.environ["FC_API_KEY"])
               if os.environ.get("FC_API_KEY") else None)
    today = date.today().isoformat()
    result = run_extraction(args.articles, args.findings, client, today,
                            scraper=scraper)

    existing = []
    for path in args.existing:
        try:
            with open(path, newline="", encoding="utf-8") as f:
                existing.extend(csv.DictReader(f))
        except OSError:
            pass
    kept, dupes = dedupe_against_existing(result["rows"], existing)
    result["rows"], result["duplicates_skipped"] = kept, dupes

    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{args.out}: {len(kept)} candidate rows "
          f"({len(result['skipped'])} skipped, {dupes} duplicates dropped)")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv))
