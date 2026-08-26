"""Minimal .env loader (stdlib only).

Local development keeps credentials in an untracked .env file (copy
.env.example). Existing environment variables always win — GitHub
Actions injects secrets via env vars, so the file is only a fallback.
"""
import os


def load_dotenv(path=".env"):
    """Load KEY=VALUE lines from `path` into os.environ (no overrides).

    Returns dict of loaded keys. Missing file is a silent no-op.
    """
    loaded = {}
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return loaded
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key:
            loaded.setdefault(key, value)
            os.environ.setdefault(key, value)
    return loaded
