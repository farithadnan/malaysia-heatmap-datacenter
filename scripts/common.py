"""Shared cross-pipeline primitives (single home — see project conventions).

Anything imported by 2+ pipeline stages lives here instead of being
duplicated per-module (review finding: UA + link digest drifted).
"""
import hashlib

# Government/press archive pages reject bare scripts via Cloudflare; a
# standard browser UA is accepted. Content fetched is public press only (§8).
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")


def link_digest(link):
    """THE file-naming contract between Fetch (writes) and Extract (reads).

    sha1(url)[:12] — if this ever changes, both stages break silently;
    tests pin the contract from both sides.
    """
    return hashlib.sha1(link.encode("utf-8")).hexdigest()[:12]
