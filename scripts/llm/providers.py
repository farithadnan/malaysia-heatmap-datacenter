"""LLM provider registry — declarative configuration, not code branches.

Adding a provider = adding one dict row here (base URL, key env var,
requirements). The factory in scripts/llm/__init__.py reads this table;
no provider-specific if/elif chains anywhere else in the project.

If the provider count ever reaches double digits, or you need fancy
features (retries, cost tracking), migrate to LiteLLM — the registry
below maps 1:1 onto its `provider/model` naming, so the seam is ready.
"""

# All well-known public endpoints for LLM providers live HERE and only here.
# (Sheet/News/Overpass endpoints live at the top of their own modules —
#  see sheets_queue.SHEETS_API_BASE, pipeline_watch.GOOGLE_NEWS_RSS_URL.)
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"

PROVIDERS = {
    "anthropic": {
        "client": "anthropic",
        "key_env": "ANTHROPIC_API_KEY",
        "requires_key": True,
        "requires_base": False,
        "default_base": None,
        "model_env": "CLAUDE_MODEL",
        "default_model": "claude-haiku-4-5-20251001",
    },
    "deepseek": {
        "client": "openai",
        "key_env": "LLM_API_KEY",
        "requires_key": True,
        "requires_base": False,
        "default_base": "https://api.deepseek.com",
        "model_env": "LLM_MODEL",
        "default_model": "deepseek-chat",
    },
    "fireworks": {
        "client": "openai",
        "key_env": "LLM_API_KEY",
        "requires_key": True,
        "requires_base": False,
        "default_base": "https://api.fireworks.ai/inference/v1",
        "model_env": "LLM_MODEL",
        "default_model": None,
    },
    "openai": {
        # Any self-hosted / third-party OpenAI-compatible API:
        # Modal-hosted vLLM, Groq, Together, OpenRouter, local LM Studio…
        "client": "openai",
        "key_env": "LLM_API_KEY",
        "requires_key": False,   # self-hosted endpoints are often unauthenticated
        "requires_base": True,
        "default_base": None,
        "model_env": "LLM_MODEL",
        "default_model": None,
    },
}

# Common names people actually type -> canonical provider keys.
ALIASES = {
    "modal": "openai",
    "modal.com": "openai",
    "fireworks.ai": "fireworks",
    "openai_compatible": "openai",
}


def resolve_provider(name):
    """Provider name/alias -> its registry spec. Raises on unknown names."""
    key = ALIASES.get((name or "").lower().strip(), (name or "").lower().strip())
    if key not in PROVIDERS:
        raise RuntimeError(f"unknown LLM_PROVIDER: {name}")
    return PROVIDERS[key]
