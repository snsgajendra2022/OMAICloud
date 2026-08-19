"""Chat reply backends: OM native (default), local engine, or OpenAI-compatible API.

Selection (``OM_AI_CHAT_BACKEND`` or ``OM_MODEL_PROVIDER``):
  - ``om_native`` (default when unset): OMNativeBackend ONLY — no third-party LLM fallback
  - ``openai`` / ``local``: explicit opt-in only
  - ``auto``: OpenAI if API key set → local OM (never Ollama)

Ollama is not part of the production path. Legacy client lives under
``om_ai.legacy.ollama`` and is never auto-imported by serve/API.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable
from zoneinfo import ZoneInfo

import httpx

from om_ai.backends.base import NativeCheckpointError

logger = logging.getLogger(__name__)

BackendName = str  # "om_native" | "local" | "openai"

_DEFAULT_BACKEND = "om_native"

# Keep identity short: local OM-1.0 configs often use max_seq_len=128, and a long
# system preamble was truncating the user turn and producing empty/garbage replies.
OM_SYSTEM_IDENTITY = (
    "You are OM AI, powered by the OM-1.0 native language model. "
    "Do not claim to be Llama, Ollama, ChatGPT, GPT, Claude, Gemini, "
    "or another third-party model."
)

OM_SYSTEM_IDENTITY_COMPACT = "You are OM AI (OM-1.0 native language model)."


@dataclass(frozen=True)
class ChatBackendInfo:
    backend: BackendName
    model: str
    detail: str = ""
    provider: str = ""
    live_knowledge: dict[str, Any] | None = None


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def openai_base_url() -> str:
    return _env("OM_AI_OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")


def openai_model() -> str:
    return _env("OM_AI_OPENAI_MODEL", "gpt-4o-mini")


def openai_api_key() -> str:
    return _env("OM_AI_OPENAI_API_KEY") or _env("OPENAI_API_KEY")


def configured_backend() -> str:
    """Resolve configured chat backend.

    Default when unset is ``om_native``. ``ollama`` is rejected in production —
    use ``om_ai.legacy.ollama`` only via explicit external scripts.
    """
    provider = (_env("OM_MODEL_PROVIDER") or "").lower()
    chat = (_env("OM_AI_CHAT_BACKEND") or _DEFAULT_BACKEND).lower()
    if provider in {"om_native", "om-native", "native", "om"}:
        return "om_native"
    if chat in {"om_native", "om-native", "native"}:
        return "om_native"
    if chat == "ollama" or provider == "ollama":
        raise RuntimeError(
            "Ollama is not part of the OM-1.0 native production path. "
            "Unset OM_AI_CHAT_BACKEND/OM_MODEL_PROVIDER or use om_native. "
            "Legacy client (opt-in scripts only): om_ai.legacy.ollama"
        )
    if provider in {"openai", "local"} and chat in {_DEFAULT_BACKEND, "auto"}:
        return provider
    if not chat:
        return _DEFAULT_BACKEND
    return chat


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
    if mode in {"openai", "local"}:
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

    # auto — never picks Ollama
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


def om_system_identity_text() -> str:
    return OM_SYSTEM_IDENTITY


def runtime_date_system_text(*, today: date | None = None) -> str:
    """Build a dynamic date/year system prompt from the real calendar date."""
    d = today or date.today()
    human = d.strftime(f"%A, %B {d.day}, %Y")
    tz_name = _env("OM_TIMEZONE") or _env("TZ") or "UTC"
    try:
        ZoneInfo(tz_name)
    except Exception:
        tz_name = "UTC"
    return (
        f"{OM_SYSTEM_IDENTITY} "
        f"Today's date is {human}. "
        f"Always treat the current year as {d.year}. "
        f"Timezone: {tz_name}."
    )


def runtime_date_system_text_compact(*, today: date | None = None) -> str:
    """Ultra-short system line for tiny context windows (e.g. max_seq_len=128)."""
    d = today or date.today()
    human = d.strftime(f"%A, %B {d.day}, %Y")
    return (
        f"{OM_SYSTEM_IDENTITY_COMPACT} "
        f"Today's date is {human}. "
        f"Always treat the current year as {d.year}."
    )


def with_runtime_date_context(
    messages: list[dict],
    *,
    today: date | None = None,
) -> list[dict[str, str]]:
    """Ensure messages include OM identity + accurate runtime date context."""
    date_line = runtime_date_system_text(today=today)
    msgs = _normalize_messages(messages)
    for i, m in enumerate(msgs):
        if m["role"] != "system":
            continue
        content = (m["content"] or "").strip()
        if "Today's date is " in content and "Always treat the current year as " in content:
            if "OM-1.0 native language model" not in content:
                msgs[i] = {"role": "system", "content": f"{OM_SYSTEM_IDENTITY}\n\n{content}"}
            return msgs
        if "Today's date is " in content and "The current year is " in content:
            if "OM-1.0 native language model" not in content:
                msgs[i] = {"role": "system", "content": f"{OM_SYSTEM_IDENTITY}\n\n{content}"}
            return msgs
        merged = f"{content}\n\n{date_line}" if content else date_line
        msgs[i] = {"role": "system", "content": merged}
        return msgs
    return [{"role": "system", "content": date_line}] + msgs


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
        # Live knowledge (HTTP/search/local) — never another LLM.
        lk_meta: dict[str, Any] = {}
        try:
            from om_ai.live_knowledge import enrich_messages_for_live_knowledge

            messages, lk_meta = enrich_messages_for_live_knowledge(messages)
        except Exception as exc:
            logger.debug("live_knowledge enrich skipped: %s", exc)

        grounded = (lk_meta.get("grounded_reply") or "").strip()
        prefer_grounded = bool(lk_meta.get("prefer_grounded_reply")) and bool(grounded)
        # Tiny OM-1.0 windows often cannot synthesize long retrieval context.
        # When live retrieval succeeded, return the grounded extractive answer
        # (still not an external LLM). Set OM_LIVE_KNOWLEDGE_GROUNDED=0 to force
        # native-only synthesis of the injected facts.
        grounded_env = (_env("OM_LIVE_KNOWLEDGE_GROUNDED") or "1").lower()
        grounded_allowed = grounded_env not in {"0", "false", "no", "off"}
        info_lk = ChatBackendInfo(
            backend=info.backend,
            model=info.model,
            detail=info.detail,
            provider=info.provider,
            live_knowledge={
                k: v
                for k, v in lk_meta.items()
                if k != "grounded_reply"  # full text already returned as reply
            }
            or None,
        )
        if prefer_grounded and grounded_allowed:
            return grounded, info_lk

        local_kwargs = dict(kwargs)
        if top_k is not None:
            local_kwargs["top_k"] = top_k
        if repetition_penalty is not None:
            local_kwargs["repetition_penalty"] = repetition_penalty
        try:
            text = native_chat(messages, **local_kwargs)
        except NativeCheckpointError:
            raise
        except Exception as exc:
            raise NativeCheckpointError(
                f"OM-1.0 checkpoint unavailable. ({exc})"
            ) from exc
        # Harden API/UI: never return whitespace-only (UI labels that "(empty reply)").
        if not (text or "").strip():
            if grounded:
                text = grounded
            else:
                text = "OM-1.0 produced no text; try again."
        return text, info_lk

    if info.backend == "openai":
        text = chat_via_openai(messages, model=info.model, **kwargs)
        return text, info

    if local_chat is None or not local_loaded:
        raise RuntimeError(
            "No chat backend available. Set OM_MODEL_PROVIDER=om_native with a real "
            "OM-1.0 checkpoint, load a local OM checkpoint (OM_AI_AUTOLOAD=1), or set "
            "OM_AI_OPENAI_API_KEY / OPENAI_API_KEY with OM_AI_CHAT_BACKEND=openai."
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
        "openai_configured": openai_configured(),
        "local_loaded": local_loaded,
        "native_ready": native_ready,
        "external_llm": "none" if info.backend == "om_native" else info.backend,
    }
