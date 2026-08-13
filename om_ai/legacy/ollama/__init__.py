"""Legacy Ollama HTTP client (opt-in only).

Not used by ``om-ai serve`` / ``om_native`` production. Import explicitly:

    from om_ai.legacy.ollama.client import chat_via_ollama
"""

from om_ai.legacy.ollama.client import (
    chat_via_ollama,
    ollama_base_url,
    ollama_model,
    ollama_reachable,
)

__all__ = [
    "chat_via_ollama",
    "ollama_base_url",
    "ollama_model",
    "ollama_reachable",
]
