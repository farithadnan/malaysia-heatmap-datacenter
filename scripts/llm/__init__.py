"""Public LLM client factory. One function in, one callable out.

    client = make_llm_client_from_env(os.environ)   # prompt -> dict | None

Provider selection, key/base/model resolution and requirements checking all
flow from env vars through the declarative registry in providers.py —
no hardcoded provider logic here.
"""
from scripts.llm import clients, providers  # noqa: F401  (public surface)
from scripts.llm.clients import (make_anthropic_client,  # noqa: F401
                                 make_openai_compatible_client)
from scripts.llm.parsing import extract_json_object  # noqa: F401
from scripts.llm.providers import PROVIDERS, resolve_provider  # noqa: F401


def make_llm_client_from_env(env, poster=None):
    """Build an LLM client callable from an env mapping.

    LLM_PROVIDER selects the registry row (aliases allowed);
    LLM_API_KEY / LLM_BASE_URL / LLM_MODEL / ANTHROPIC_API_KEY / CLAUDE_MODEL
    fill the slots declared by that row.
    """
    kwargs = {} if poster is None else {"poster": poster}
    spec = resolve_provider(env.get("LLM_PROVIDER") or "anthropic")

    key = env.get(spec["key_env"] or "") if spec["key_env"] else None
    if spec["requires_key"] and not key:
        raise RuntimeError(
            f"LLM_PROVIDER requires {spec['key_env']} (see .env.example)")

    base = env.get("LLM_BASE_URL") or spec["default_base"]
    if spec["requires_base"] and not base:
        raise RuntimeError("LLM_PROVIDER requires LLM_BASE_URL (see .env.example)")

    model = env.get(spec["model_env"] or "") if spec["model_env"] else None
    model = model or env.get("LLM_MODEL") or spec["default_model"]
    if not model:
        raise RuntimeError("LLM_PROVIDER requires a model (LLM_MODEL or provider default)")

    if spec["client"] == "anthropic":
        return clients.make_anthropic_client(key, model, **kwargs)
    return clients.make_openai_compatible_client(base, key, model, **kwargs)

