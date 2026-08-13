"""Chat reply backends: OM native, local engine, Ollama, or OpenAI-compatible API.

Selection (``OM_AI_CHAT_BACKEND`` or ``OM_MODEL_PROVIDER``):
  - ``om_native`` (default when unset): OMNativeBackend ONLY — no Ollama/OpenAI fallback
  - ``ollama`` / ``openai`` / ``local``: force that path (Ollama is explicit opt-in only)
  - ``auto``: OpenAI if API key set → local OM (never auto-picks Ollama)
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

import httpx

from om_ai.backends.base import NativeCheckpointError

logger = logging.getLogger(__name__)

BackendName = str  # "om_native" | "local" | "ollama" | "openai"

_DEFAULT_BACKEND = "om_native"


@dataclass(frozen=True)
class ChatBackendInfo:
    backend: BackendName
    model: str
    detail: str = ""
    provider: str = ""


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
    """Resolve configured chat backend.

    Default when unset is ``om_native``. Explicit ``ollama`` keeps Ollama only
    when requested — never selected by default or by ``auto``.
    """
    provider = (_env("OM_MODEL_PROVIDER") or "").lower()
    chat = (_env("OM_AI_CHAT_BACKEND") or _DEFAULT_BACKEND).lower()
    if provider in {"om_native", "om-native", "native"}:
        return "om_native"
    if chat in {"om_native", "om-native", "native"}:
        return "om_native"
    if provider in {"ollama", "openai", "local"} and chat in {_DEFAULT_BACKEND, "auto"}:
        return provider
    if not chat:
        return _DEFAULT_BACKEND
    return chat


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


def resolve_backend(*, local_loaded: bool = False, native_ready: bool = False) -> ChatBackendInfo:
    """Pick the active chat backend for this process."""
    mode = configured_backend()
    if mode == "om_native":
        return ChatBackendInfo(
            "om_native",
            _env("OM_MODEL_ID", "OM-1.0") or "OM-1.0",
            "OM_MODEL_PROVIDER/OM_AI_CHAT_BACKEND=om_native (default)"
            + (" (ready)" if native_ready else " (checkpoint required)"),
            provider="OM AI",
        )
    if mode in {"ollama", "openai", "local"}:
        if mode == "ollama":
            return ChatBackendInfo(
                "ollama",
                ollama_model(),
                "forced by OM_AI_CHAT_BACKEND=ollama",
                provider="Ollama",
            )
        if mode == "openai":
            return ChatBackendInfo(
                "openai",
                openai_model(),
                "forced by OM_AI_CHAT_BACKEND=openai",
                provider="OpenAI",
            )
        return ChatBackendInfo(
            "local",
            _env("OM_AI_MODEL_ID", "om-tiny") or "om-tiny",
            "forced by OM_AI_CHAT_BACKEND=local",
            provider="OM AI",
        )

    # auto — never picks Ollama; use OM_AI_CHAT_BACKEND=ollama for that
    if openai_configured():
        return ChatBackendInfo(
            "openai", openai_model(), "auto: OpenAI API key present", provider="OpenAI"
        )
    return ChatBackendInfo(
        "local",
        _env("OM_AI_MODEL_ID", "om-tiny") or "om-tiny",
        "auto: local OM" + (" (loaded)" if local_loaded else " (may be unloaded)"),
        provider="OM AI",
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


def runtime_date_system_text(*, today: date | None = None) -> str:
    """Build a dynamic date/year system prompt from the real calendar date."""
    d = today or date.today()
    # Example: Wednesday, August 13, 2026
    human = d.strftime(f"%A, %B {d.day}, %Y")
    return (
        f"You are OM AI. Today's date is {human}. "
        f"Always treat the current year as {d.year}. "
        "Do not claim the year is 2023 or cite a 2023 knowledge cutoff as the present. "
        "If asked about events after your training data, say you may lack post-training "
        "details and answer carefully without inventing news."
    )


def with_runtime_date_context(
    messages: list[dict],
    *,
    today: date | None = None,
) -> list[dict[str, str]]:
    """Ensure messages include accurate runtime date context.

    If a system message already exists, keep its content and append the date
    line. Otherwise prepend a new system message.
    """
    date_line = runtime_date_system_text(today=today)
    msgs = _normalize_messages(messages)
    for i, m in enumerate(msgs):
        if m["role"] != "system":
            continue
        content = (m["content"] or "").strip()
        # Avoid duplicating if runtime date framing is already present.
        if "Today's date is " in content and "Always treat the current year as " in content:
            return msgs
        # Legacy phrasing from an earlier injector — do not stack another date block.
        if "Today's date is " in content and "The current year is " in content:
            return msgs
        merged = f"{content}\n\n{date_line}" if content else date_line
        msgs[i] = {"role": "system", "content": merged}
        return msgs
    return [{"role": "system", "content": date_line}] + msgs


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
    native_chat: Callable[..., str] | None = None,
    native_ready: bool = False,
    max_new_tokens: int = 256,
    temperature: float = 0.8,
    top_p: float = 1.0,
    top_k: int | None = None,
    repetition_penalty: float | None = None,
) -> tuple[str, ChatBackendInfo]:
    """Generate a chat reply and return ``(text, backend_info)``."""
    messages = with_runtime_date_context(messages)
    info = resolve_backend(local_loaded=local_loaded, native_ready=native_ready)
    kwargs: dict[str, Any] = {
        "max_new_tokens": max_new_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }

    # --- OM native: NO silent Ollama/OpenAI fallback ---
    if info.backend == "om_native":
        if native_chat is None or not native_ready:
            raise NativeCheckpointError("OM-1.0 checkpoint unavailable.")
        local_kwargs = dict(kwargs)
        if top_k is not None:
            local_kwargs["top_k"] = top_k
        if repetition_penalty is not None:
            local_kwargs["repetition_penalty"] = repetition_penalty
        try:
            return native_chat(messages, **local_kwargs), info
        except NativeCheckpointError:
            raise
        except Exception as exc:
            # Surface as checkpoint/runtime failure — still no Ollama proxy.
            raise NativeCheckpointError(
                f"OM-1.0 checkpoint unavailable. ({exc})"
            ) from exc

    if info.backend == "ollama":
        try:
            text = chat_via_ollama(messages, model=info.model, **kwargs)
            return text, info
        except Exception as exc:
            # Only fall back when NOT in om_native mode (already handled above).
            logger.warning("Ollama chat failed (%s); falling back", exc)
            if openai_configured():
                info = ChatBackendInfo(
                    "openai",
                    openai_model(),
                    f"fallback after Ollama error: {exc}",
                    provider="OpenAI",
                )
                text = chat_via_openai(messages, model=info.model, **kwargs)
                return text, info
            if local_chat is not None and local_loaded:
                info = ChatBackendInfo(
                    "local",
                    _env("OM_AI_MODEL_ID", "om-tiny") or "om-tiny",
                    f"fallback after Ollama error: {exc}",
                    provider="OM AI",
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
            "No chat backend available. Set OM_MODEL_PROVIDER=om_native with a real "
            "checkpoint, load a local OM checkpoint (OM_AI_AUTOLOAD=1), set "
            "OM_AI_OPENAI_API_KEY / OPENAI_API_KEY, or explicitly set "
            "OM_AI_CHAT_BACKEND=ollama with Ollama running."
        )
    local_kwargs = dict(kwargs)
    if top_k is not None:
        local_kwargs["top_k"] = top_k
    if repetition_penalty is not None:
        local_kwargs["repetition_penalty"] = repetition_penalty
    return local_chat(messages, **local_kwargs), info


def backend_status(*, local_loaded: bool = False, native_ready: bool = False) -> dict[str, Any]:
    info = resolve_backend(local_loaded=local_loaded, native_ready=native_ready)
    return {
        "backend": info.backend,
        "model": info.model,
        "provider": info.provider,
        "detail": info.detail,
        "configured": configured_backend(),
        "ollama_url": ollama_base_url() if configured_backend() == "ollama" else None,
        "ollama_reachable": (
            ollama_reachable() if configured_backend() == "ollama" else None
        ),
        "openai_configured": openai_configured(),
        "local_loaded": local_loaded,
        "native_ready": native_ready,
    }
