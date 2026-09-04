"""Legacy adapters — connected to serve via connectivity_bridge (opt-in Ollama)."""
from __future__ import annotations

__all__ = ["ollama_available", "get_ollama_client"]


def ollama_available() -> bool:
    import os

    return os.environ.get("OM_LEGACY_OLLAMA", "0").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def get_ollama_client():
    """Return legacy Ollama client only when OM_LEGACY_OLLAMA=1."""
    if not ollama_available():
        return None
    from om_ai.legacy.ollama import client

    return client
