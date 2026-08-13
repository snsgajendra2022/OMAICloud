"""Legacy Ollama chat client — explicit import only; never auto-wired into serve."""
from __future__ import annotations

import os

import httpx


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def ollama_base_url() -> str:
    return _env("OM_AI_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")


def ollama_model() -> str:
    return _env("OM_AI_OLLAMA_MODEL", "llama3.2")


def ollama_reachable(timeout: float = 1.5) -> bool:
    url = f"{ollama_base_url()}/api/tags"
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url)
            return r.status_code < 500
    except Exception:
        return False


def chat_via_ollama(
    messages: list[dict],
    *,
    max_new_tokens: int = 256,
    temperature: float = 0.8,
    top_p: float = 1.0,
    model: str | None = None,
) -> str:
    payload = {
        "model": model or ollama_model(),
        "messages": [
            {"role": str(m.get("role") or "user"), "content": str(m.get("content") or "")}
            for m in messages
        ],
        "stream": False,
        "options": {
            "temperature": float(temperature),
            "top_p": float(top_p),
            "num_predict": int(max_new_tokens),
        },
    }
    url = f"{ollama_base_url()}/api/chat"
    with httpx.Client(timeout=120.0) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    msg = data.get("message") or {}
    text = msg.get("content")
    if not isinstance(text, str):
        raise RuntimeError(f"Ollama returned unexpected payload: {data!r}")
    return text
