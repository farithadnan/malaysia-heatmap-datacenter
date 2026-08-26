"""Extract stage (spec §8, stage 3): pull structured data-center facts out of
article text with an LLM — provider-agnostic (spec: "Claude API **or another
LLM API**").

Supported providers, selected via env (`.env` locally, Actions secrets in CI):

    anthropic   Anthropic Messages API      (ANTHROPIC_API_KEY, CLAUDE_MODEL?)
    deepseek    DeepSeek (OpenAI-compat)    (LLM_API_KEY, LLM_MODEL=deepseek-chat)
    openai      Any OpenAI-compatible API   (LLM_API_KEY, LLM_BASE_URL, LLM_MODEL)
                — incl. Modal-hosted models, Groq, Together, OpenRouter…

Scraping (article → clean text) is a separate seam: local `html_to_text` by
default, or Firecrawl (`FC_API_KEY`) for JS-heavy pages.

Every fact row carries its source URL + extraction date (spec); rows failing
the spec §5 schema are dropped with a reason; texts with no relevant facts
produce nothing.
"""
import argparse
import glob
import json
import os
import re
import urllib.request
from datetime import date
from html.parser import HTMLParser

from scripts.csv_to_geojson import SCHEMA
from scripts.env import load_dotenv

ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"
FIRECRAWL_SCRAPE_URL = "https://api.firecrawl.dev/v1/scrape"
DEFAULT_CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
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


def _post_json(url, headers, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def make_firecrawl_scraper(api_key, poster=_post_json):
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


def extract_json_object(text):
    """First JSON object in text (tolerates ```json fences, prose padding)."""
    if not text:
        return None
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidate = m.group(1) if m else None
    if candidate is None:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            return None
        candidate = text[start:end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def make_anthropic_client(api_key, model=DEFAULT_CLAUDE_MODEL, poster=_post_json):
    def call(article_text):
        resp = poster(
            ANTHROPIC_MESSAGES_URL,
            {"x-api-key": api_key, "anthropic-version": "2023-06-01",
             "Content-Type": "application/json"},
            {"model": model, "max_tokens": 512,
             "messages": [{"role": "user", "content": build_prompt(article_text)}]})
        text = "".join(b.get("text", "") for b in resp.get("content", []))
        return extract_json_object(text)
    return call


def make_openai_compatible_client(base_url, api_key, model, poster=_post_json):
    """Any OpenAI-compatible /chat/completions API (Modal, Fireworks, DeepSeek,
    Groq, Together, OpenRouter…). Auth header is omitted when api_key is empty
    (many self-hosted/Modal endpoints are unauthenticated). A missing "/v1"
    suffix on base_url is auto-corrected — the #1 config fumble."""
    base = base_url.rstrip("/")
    if not re.search(r"/v\d+$", base):
        base += "/v1"

    def call(article_text):
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        resp = poster(
            f"{base}/chat/completions", headers,
            {"model": model, "max_tokens": 512,
             "messages": [{"role": "user", "content": build_prompt(article_text)}]})
        text = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        return extract_json_object(text)
    return call


def make_llm_client_from_env(env, poster=_post_json):
    """Provider factory. Provider VALUES are env/config-driven, not hardcoded:

    anthropic | deepseek | fireworks[.ai] | openai | openai_compatible |
    modal | modal.com   (last two = OpenAI-compatible aliases)
    """
    provider = (env.get("LLM_PROVIDER") or "anthropic").lower().strip()
    if provider == "anthropic":
        key = env.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY")
        return make_anthropic_client(key, env.get("CLAUDE_MODEL", DEFAULT_CLAUDE_MODEL), poster)

    if provider == "deepseek":
        if not env.get("LLM_API_KEY"):
            raise RuntimeError("LLM_PROVIDER=deepseek requires LLM_API_KEY")
        return make_openai_compatible_client(
            DEEPSEEK_BASE_URL, env["LLM_API_KEY"], env.get("LLM_MODEL", "deepseek-chat"), poster)

    if provider in ("fireworks", "fireworks.ai"):
        base = env.get("LLM_BASE_URL") or FIREWORKS_BASE_URL
        return make_openai_compatible_client(
            base, env.get("LLM_API_KEY"), env.get("LLM_MODEL"), poster)

    if provider in ("openai", "openai_compatible", "modal", "modal.com"):
        base = env.get("LLM_BASE_URL")
        if not base:
            raise RuntimeError(f"LLM_PROVIDER={provider} requires LLM_BASE_URL")
        if not env.get("LLM_MODEL"):
            raise RuntimeError(f"LLM_PROVIDER={provider} requires LLM_MODEL")
        # key optional: Modal/self-hosted endpoints are often unauthenticated
        return make_openai_compatible_client(
            base, env.get("LLM_API_KEY"), env["LLM_MODEL"], poster)

    raise RuntimeError(f"unknown LLM_PROVIDER: {provider}")

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
    parsed = llm_client(article_text)
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
        "capacity_mw": str(parsed.get("capacity_mw") or "").replace("MW", "").strip(),
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
    return kept, skipped


def sha1_digest(text):
    import hashlib
    return hashlib.sha1(text.encode()).hexdigest()[:12]


def run_extraction(articles_dir, findings_path, llm_client, today, scraper=None):
    """All .html/.md articles from a watch/fetch sweep -> schema rows + skip log."""
    with open(findings_path, encoding="utf-8") as f:
        findings = json.load(f)
    by_digest = {}
    for a in findings.get("articles", []):
        by_digest[sha1_digest(a["link"])] = a

    rows, skipped = [], []
    for path in sorted(glob.glob(os.path.join(articles_dir, "*.*"))):
        digest = os.path.splitext(os.path.basename(path))[0]
        if path.endswith(".pdf"):
            skipped.append({"digest": digest, "reason": "PDF — deferred to Issue #15"})
            continue
        link = None
        for d, a in by_digest.items():
            if d == digest:
                link = a["link"]
                break
        source = link or f"{articles_dir}/{digest}"
        if scraper and link:
            text = scraper(link)
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
    today = date.today().isoformat()
    result = run_extraction(args.articles, args.findings, client, today)

    import csv
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
