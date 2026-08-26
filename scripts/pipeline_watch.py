"""Watch stage of the data-collection pipeline (spec §8, stage 1).

Two mechanisms:
  1. RSS watch — standing Google News searches (no account needed).
  2. Page snapshots — hash-and-diff for sources without RSS (e.g. MIDA/TNB
     newsroom pages): a page is flagged when its content hash changes.

Stdlib only. Network is injectable everywhere so tests stay offline.

CLI:
    python3 scripts/pipeline_watch.py --config data/sources.json \
        --out data/raw/watch-YYYY-MM-DD.json --state data/raw/page-state.json
"""
import argparse
import hashlib
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

# Government/press archive pages reject bare scripts via Cloudflare; a standard
# browser UA is accepted. Content fetched is public press material only (spec §8).
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def hash_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_rss(xml_text):
    """RSS 2.0 XML -> list of {title, link, published} dicts."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise ValueError(f"malformed feed: {e}") from e
    if root.tag != "rss":
        raise ValueError(f"not an RSS document: <{root.tag}>")
    items = []
    for item in root.iter("item"):
        items.append({
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "published": (item.findtext("pubDate") or "").strip(),
        })
    return items


# Public endpoint homes (one place only). Source URLs themselves live in
# data/sources.json — configuration, not code.
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


def google_news_rss_url(query):
    """Standing search feed URL, localized to Malaysia (spec §8)."""
    return (GOOGLE_NEWS_RSS_URL + "?"
            + urllib.parse.urlencode({"q": query, "hl": "en-MY", "gl": "MY", "ceid": "MY:en"}))


def dedupe_by_link(items):
    """First occurrence wins; preserves order."""
    seen, out = set(), []
    for item in items:
        key = item.get("link") or item.get("title")
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def snapshot_pages(pages, state, fetcher):
    """Hash-and-diff page monitor.

    pages: [{"name", "url"}];  state: {name: last_hash};  fetcher: url -> str
    A page counts as changed on first sight (baseline capture) or hash change.
    Returns (changed_pages, new_state).
    """
    changed, new_state = [], dict(state)
    for page in pages:
        content = fetcher(page["url"])
        digest = hash_text(content)
        if state.get(page["name"]) != digest:
            changed.append(page)
            new_state[page["name"]] = digest
    return changed, new_state


def fetch_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def load_sources(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run(config_path, state_path, fetcher=fetch_text, today=None):
    config = load_sources(config_path)
    today = today or date.today().isoformat()

    articles, errors = [], []
    for feed in config.get("rss_feeds", []):
        try:
            xml = fetcher(feed["url"])
            for item in parse_rss(xml):
                item["source_feed"] = feed["name"]
                articles.append(item)
        except Exception as e:  # one bad source must not kill the watch run
            errors.append(f"{feed['name']}: {e}")
    articles = dedupe_by_link(articles)

    try:
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, json.JSONDecodeError):
        state = {}
    try:
        pages_changed, state = snapshot_pages(config.get("pages", []), state, fetcher)
    except Exception as e:
        pages_changed = []
        errors.append(f"page snapshots: {e}")

    return {
        "date": today,
        "articles": articles,
        "pages_changed": pages_changed,
        "errors": errors,
    }, state


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--state", required=True)
    args = ap.parse_args(argv[1:])

    findings, state = run(args.config, args.state)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(findings, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(args.state, "w", encoding="utf-8", newline="\n") as f:
        json.dump(state, f, indent=2)
        f.write("\n")
    print(f"{args.out}: {len(findings['articles'])} articles, "
          f"{len(findings['pages_changed'])} page changes")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv))
