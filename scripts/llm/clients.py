"""HTTP client implementations for the two API dialects we speak.

Clients receive a READY-BUILT prompt string and return the parsed JSON
object (or None when the reply contains no JSON). They own NO extraction
or prompt logic — that lives in scripts/pipeline_extract.py — and no
provider selection logic — that lives in scripts/llm/providers.py.

`poster` is injectable everywhere so tests never touch the network.
"""
import json
import re
import urllib.request

from scripts.llm.parsing import extract_json_object
from scripts.llm.providers import ANTHROPIC_MESSAGES_URL

MAX_TOKENS = 512   # extraction replies are small; keep both dialects cheap alike


def post_json(url, headers, body):
    """Shared JSON-over-HTTP POST (the only transport primitive we need)."""
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def make_anthropic_client(api_key, model, poster=post_json):
    """Anthropic Messages API."""
    def call(prompt_text):
        resp = poster(
            ANTHROPIC_MESSAGES_URL,
            {"x-api-key": api_key, "anthropic-version": "2023-06-01",
             "Content-Type": "application/json"},
            {"model": model, "max_tokens": MAX_TOKENS,
             "messages": [{"role": "user", "content": prompt_text}]})
        text = "".join(b.get("text", "") for b in resp.get("content", []))
        return extract_json_object(text)
    return call


def make_openai_compatible_client(base_url, api_key, model, poster=post_json):
    """Any OpenAI-style /chat/completions API (Modal vLLM, DeepSeek,
    Fireworks, Groq, Together, OpenRouter…).

    - Authorization header omitted when api_key is empty
    - missing "/v<N>" suffix on base_url is auto-corrected
    """
    base = base_url.rstrip("/")
    if not re.search(r"/v\d+$", base):
        base += "/v1"

    def call(prompt_text):
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        resp = poster(
            f"{base}/chat/completions", headers,
            {"model": model, "max_tokens": MAX_TOKENS,
             "messages": [{"role": "user", "content": prompt_text}]})
        text = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        return extract_json_object(text)
    return call
