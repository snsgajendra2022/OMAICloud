"""Chat reply backends: local OM engine, Ollama, or OpenAI-compatible API.

Selection (``OM_AI_CHAT_BACKEND``):
  - ``auto`` (default): Ollama if reachable → OpenAI if API key set → local OM
  - ``ollama`` / ``openai`` / ``local``: force that path

The local tiny demo checkpoint often produces gibberish; prefer Ollama or
OpenAI for coherent English until a capable OM checkpoint is loaded.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Callable

import httpx

logger = logging.getLogger(__name__)

BackendName = str  # "local" | "ollama" | "openai"


@dataclass(frozen=True)
class ChatBackendInfo:
    backend: BackendName
    model: str
    detail: str = ""


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def ollama_base_url() -> str:
    return _env("OM_AI_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")


def ollama_model() -> str:
    return _env("OM_AI_OLLAMA_MODEL", "llama3.2")


def openai_base_url() -> str:
    return _env("OM_AI_OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")


def openai_model() -> str:
    return _env("OM_AI_OPENAI_MODEL", "gpt-4o-mini")


def openai_api_key() -> str:
    return _env("OM_AI_OPENAI_API_KEY") or _env("OPENAI_API_KEY")


def configured_backend() -> str:
    return (_env("OM_AI_CHAT_BACKEND", "auto") or "auto").lower()


def ollama_reachable(timeout: float = 1.5) -> bool:
    url = f"{ollama_base_url()}/api/tags"
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url)
            return r.status_code < 500
    except Exception:
        return False


def openai_configured() -> bool:
    return bool(openai_api_key())


def resolve_backend(*, local_loaded: bool = False) -> ChatBackendInfo:
    """Pick the active chat backend for this process."""
    mode = configured_backend()
    if mode in {"ollama", "openai", "local"}:
        if mode == "ollama":
            return ChatBackendInfo("ollama", ollama_model(), "forced by OM_AI_CHAT_BACKEND=ollama")
        if mode == "openai":
            return ChatBackendInfo("openai", openai_model(), "forced by OM_AI_CHAT_BACKEND=openai")
        return ChatBackendInfo(
            "local",
            _env("OM_AI_MODEL_ID", "om-tiny") or "om-tiny",
            "forced by OM_AI_CHAT_BACKEND=local",
        )

    # auto
    if ollama_reachable():
        return ChatBackendInfo("ollama", ollama_model(), "auto: Ollama reachable")
    if openai_configured():
        return ChatBackendInfo("openai", openai_model(), "auto: OpenAI API key present")
    return ChatBackendInfo(
        "local",
        _env("OM_AI_MODEL_ID", "om-tiny") or "om-tiny",
        "auto: local OM" + (" (loaded)" if local_loaded else " (may be unloaded)"),
    )


def _normalize_messages(messages: list[dict]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for m in messages:
        role = str(m.get("role") or "user")
        content = m.get("content")
        if content is None:
            content = ""
        elif not isinstance(content, str):
            content = str(content)
        out.append({"role": role, "content": content})
    return out


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
        "messages": _normalize_messages(messages),
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


def chat_via_openai(
    messages: list[dict],
    *,
    max_new_tokens: int = 256,
    temperature: float = 0.8,
    top_p: float = 1.0,
    model: str | None = None,
) -> str:
    key = openai_api_key()
    if not key:
        raise RuntimeError("OpenAI API key not set (OM_AI_OPENAI_API_KEY or OPENAI_API_KEY)")
    payload = {
        "model": model or openai_model(),
        "messages": _normalize_messages(messages),
        "max_tokens": int(max_new_tokens),
        "temperature": float(temperature),
        "top_p": float(top_p),
    }
    url = f"{openai_base_url()}/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=120.0) as client:
        r = client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
    try:
        return str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"OpenAI-compatible API returned unexpected payload: {data!r}") from exc


def chat_reply(
    messages: list[dict],
    *,
    local_chat: Callable[..., str] | None = None,
    local_loaded: bool = False,
    max_new_tokens: int = 256,
    temperature: float = 0.8,
    top_p: float = 1.0,
    top_k: int | None = None,
    repetition_penalty: float | None = None,
) -> tuple[str, ChatBackendInfo]:
    """Generate a chat reply and return ``(text, backend_info)``."""
    info = resolve_backend(local_loaded=local_loaded)
    kwargs: dict[str, Any] = {
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }

    if info.backend == "ollama":
        try:
            text = chat_via_ollama(messages, model=info.model, **kwargs)
            return text, info
        except Exception as exc:
            logger.warning("Ollama chat failed (%s); falling back", exc)
            if openai_configured():
                info = ChatBackendInfo("openai", openai_model(), f"fallback after Ollama error: {exc}")
                text = chat_via_openai(messages, model=info.model, **kwargs)
                return text, info
            if local_chat is not None and local_loaded:
                info = ChatBackendInfo(
                    "local",
                    _env("OM_AI_MODEL_ID", "om-tiny") or "om-tiny",
                    f"fallback after Ollama error: {exc}",
                )
                local_kwargs = dict(kwargs)
                if top_k is not None:
                    local_kwargs["top_k"] = top_k
                if repetition_penalty is not None:
                    local_kwargs["repetition_penalty"] = repetition_penalty
                return local_chat(messages, **local_kwargs), info
            raise

    if info.backend == "openai":
        text = chat_via_openai(messages, model=info.model, **kwargs)
        return text, info

    if local_chat is None or not local_loaded:
        raise RuntimeError(
            "No chat backend available. Install/start Ollama (OM_AI_CHAT_BACKEND=ollama), "
            "set OM_AI_OPENAI_API_KEY / OPENAI_API_KEY, or load a local OM checkpoint "
            "(OM_AI_AUTOLOAD=1)."
        )
    local_kwargs = dict(kwargs)
    if top_k is not None:
        local_kwargs["top_k"] = top_k
    if repetition_penalty is not None:
        local_kwargs["repetition_penalty"] = repetition_penalty
    return local_chat(messages, **local_kwargs), info


def backend_status(*, local_loaded: bool = False) -> dict[str, Any]:
    info = resolve_backend(local_loaded=local_loaded)
    return {
        "backend": info.backend,
        "model": info.model,
        "detail": info.detail,
        "configured": configured_backend(),
        "ollama_url": ollama_base_url(),
        "ollama_reachable": ollama_reachable() if info.backend == "ollama" or configured_backend() in {"auto", "ollama"} else None,
        "openai_configured": openai_configured(),
        "local_loaded": local_loaded,
    }
