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


def _latest_user_text(messages: list[dict]) -> str:
    for m in reversed(messages or []):
        if str(m.get("role") or "") == "user":
            text = str(m.get("content") or "").strip()
            # Strip legacy UI tool tags that poison tiny chat-SFT greets.
            for tag in ("[web search enabled]", "[code interpreter enabled]"):
                text = text.replace(tag, "").strip()
            return text
    return ""


def looks_like_web_spam(text: str) -> bool:
    """Detect pasted search/wiki marketing text that must never be shown as chat."""
    s = (text or "").strip()
    if not s:
        return False
    low = s.lower()
    spam_bits = (
        "enjoy the videos and music you love",
        "upload original content",
        "the correct form is",
        "the preferred form",
        "preferred form",
        "country code top-level domain",
        "live knowledge (retrieved",
        "om-1.0 should treat the facts",
        "youtube.com",
        "en.wikipedia.org",
        "upgrade upgrade",
        "membership of",
        "harry potter",
        "knockoff",
        "overpriced",
        "documentary presence",
        "released label",
        "on dvd",
        "sale by",
        "http://",
        "https://",
        "www.",
        "email@",
        "href=",
    )
    if any(b in low for b in spam_bits):
        return True
    # Long multi-topic dumps with no clear assistant voice.
    if len(s) > 180 and s.count(".") >= 4 and (" and " in low) and ("the " in low):
        markers = ("hi!", "hello", "i'm om", "i am om", "how can i help")
        if not any(m in low for m in markers):
            return True
    return False


@dataclass(frozen=True)
class ChatBackendInfo:
    backend: BackendName
    model: str
    detail: str = ""
    provider: str = ""
    live_knowledge: dict[str, Any] | None = None


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _env_float(name: str, default: float) -> float:
    raw = _env(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


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
    return f"You are OM AI. Today is {d.isoformat()} ({d.year})."


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
    max_new_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    repetition_penalty: float | None = None,
    tenant_id: str = "default",
    actor: str = "",
    assistant_instructions: str = "",
    project_instructions: str = "",
    project_id: str | None = None,
) -> tuple[str, ChatBackendInfo]:
    """Generate a chat reply and return ``(text, backend_info)``."""
    # Sanitize legacy UI tool tags from user turns.
    cleaned_messages = []
    for m in messages or []:
        role = str(m.get("role") or "user")
        content = str(m.get("content") or "")
        if role == "user":
            for tag in ("[web search enabled]", "[code interpreter enabled]"):
                content = content.replace(tag, "")
            content = content.strip()
        cleaned_messages.append({"role": role, "content": content})
    messages = cleaned_messages
    from om_ai.runtime.chat_orchestrator import (
        build_chat_messages,
        generation_config,
        is_low_quality_reply,
        looks_like_assistant_chitchat,
        policy_recovery_reply,
    )
    from om_ai.runtime.intelligence import enrich_for_chat

    info = resolve_backend(local_loaded=local_loaded, native_ready=native_ready)
    # Tiny OM-1.0 chat-SFT collapses with UI defaults (temp 0.7–0.8, 1024 tokens).
    # Prefer env/sampling defaults unless the client asks for a low temperature.
    if info.backend == "om_native":
        env_temp = _env_float("OM_CHAT_TEMPERATURE", 0.2)
        env_max = _env_int("OM_CHAT_MAX_NEW_TOKENS", 64)
        if temperature is None or float(temperature) > 0.35:
            temperature = env_temp
        if max_new_tokens is None or int(max_new_tokens) > env_max:
            max_new_tokens = env_max
    gen = generation_config(
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        repetition_penalty=repetition_penalty,
    )
    kwargs: dict[str, Any] = {
        "max_new_tokens": int(gen["max_new_tokens"]),
        "temperature": float(gen["temperature"]),
        "top_p": float(gen["top_p"]),
        "top_k": int(gen["top_k"]),
        "repetition_penalty": float(gen["repetition_penalty"]),
        "min_new_tokens": int(gen["min_new_tokens"]),
    }

    if not assistant_instructions:
        for m in messages or []:
            if str(m.get("role") or "") == "system":
                content = str(m.get("content") or "").strip()
                if content and "Today's date" not in content:
                    assistant_instructions = content
                    break

    intel = enrich_for_chat(
        messages,
        tenant_id=tenant_id or "default",
        actor=actor or "",
        assistant_instructions=assistant_instructions or "",
        project_instructions=project_instructions or "",
        project_id=project_id,
        compact=True,
    )

    # --- OM native: NO silent Ollama/OpenAI fallback ---
    if info.backend == "om_native":
        if native_chat is None or not native_ready:
            raise NativeCheckpointError("OM-1.0 checkpoint unavailable.")
        from om_ai.runtime.engine import EMPTY_GENERATION_FALLBACK, usable_generation_text

        user_text = _latest_user_text(messages)
        from om_ai.live_knowledge.freshness import is_greeting_like, is_om_self_query

        # Tiny local windows: keep sampling close to greedy so SFT chat sticks.
        if is_greeting_like(user_text) or is_om_self_query(user_text):
            kwargs["temperature"] = min(float(kwargs["temperature"]), 0.15)
            kwargs["top_k"] = min(int(kwargs["top_k"]), 20)
            kwargs["top_p"] = min(float(kwargs["top_p"]), 0.85)
            kwargs["max_new_tokens"] = min(int(kwargs["max_new_tokens"]), 48)
            kwargs["min_new_tokens"] = 1
            kwargs["repetition_penalty"] = max(float(kwargs["repetition_penalty"]), 1.05)

        info_base = ChatBackendInfo(
            backend=info.backend,
            model=info.model,
            detail=info.detail,
            provider=info.provider,
            live_knowledge={"intelligence": intel.meta} if intel.meta else None,
        )
        if intel.direct_reply:
            return intel.direct_reply, info_base

        # Prefer a single short system for tiny OM-1.0 windows.
        # Do NOT stack extra system lines — that breaks chat-SFT greets.
        if is_greeting_like(user_text) or is_om_self_query(user_text):
            extra = None
        else:
            extra = runtime_date_system_text_compact()
            if intel.extra_system:
                hint = intel.extra_system.strip()
                if len(hint) > 120:
                    hint = hint[:117] + "..."
                extra = f"{extra}\n{hint}" if extra else hint

        # Chat template: system + turns. Compact for tiny local windows.
        messages = build_chat_messages(
            messages,
            compact=True,
            extra_system=extra,
        )
        # Skip live web for greetings / OM-self so chat never becomes paste spam.
        skip_live = is_greeting_like(user_text) or is_om_self_query(user_text)

        lk_meta: dict[str, Any] = {}
        if not skip_live:
            try:
                from om_ai.live_knowledge import enrich_messages_for_live_knowledge

                messages, lk_meta = enrich_messages_for_live_knowledge(messages)
            except Exception as exc:
                logger.debug("live_knowledge enrich skipped: %s", exc)

        grounded = (lk_meta.get("grounded_reply") or "").strip()
        if grounded:
            from om_ai.live_knowledge.engine import strip_live_knowledge_boilerplate

            grounded = strip_live_knowledge_boilerplate(grounded)
            if looks_like_web_spam(grounded):
                grounded = ""
        prefer_grounded = bool(lk_meta.get("prefer_grounded_reply")) and bool(grounded)
        grounded_env = (_env("OM_LIVE_KNOWLEDGE_GROUNDED") or "0").lower()
        grounded_allowed = (
            grounded_env not in {"0", "false", "no", "off"} and not skip_live
        )
        merged_lk = {
            **({k: v for k, v in lk_meta.items() if k != "grounded_reply"} or {}),
            "intelligence": intel.meta,
        }
        info_lk = ChatBackendInfo(
            backend=info.backend,
            model=info.model,
            detail=info.detail,
            provider=info.provider,
            live_knowledge=merged_lk or None,
        )
        if prefer_grounded and grounded_allowed and grounded:
            return grounded, info_lk

        try:
            text = native_chat(messages, **kwargs)
        except NativeCheckpointError:
            raise
        except Exception as exc:
            raise NativeCheckpointError(
                f"OM-1.0 checkpoint unavailable. ({exc})"
            ) from exc

        fail = is_low_quality_reply(text)
        if not fail and is_greeting_like(user_text) and not looks_like_assistant_chitchat(text):
            fail = "spam"
        if not fail and is_om_self_query(user_text):
            low = (text or "").lower()
            if "om" not in low:
                fail = "spam"
        if not fail:
            cleaned = usable_generation_text(text) or ""
            cleaned = cleaned.lstrip(" ,.;:\"'`-—–")
            if cleaned:
                return cleaned, info_lk

        if grounded_allowed and grounded and not looks_like_web_spam(grounded):
            return grounded, info_lk

        # Safer OM-1.0 retry with stronger anti-repetition.
        try:
            retry_kwargs = dict(kwargs)
            retry_kwargs.update(
                {
                    "max_new_tokens": max(int(kwargs["max_new_tokens"]), 96),
                    "temperature": 0.55,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repetition_penalty": max(float(kwargs["repetition_penalty"]), 1.2),
                    "min_new_tokens": 8,
                }
            )
            retry = native_chat(messages, **retry_kwargs)
            retry_fail = is_low_quality_reply(retry)
            if not retry_fail:
                retry = (usable_generation_text(retry) or "").lstrip(" ,.;:\"'`-—–")
                if retry:
                    return retry, info_lk
            else:
                fail = retry_fail
        except Exception as exc:
            logger.debug("native retry skipped: %s", exc)

        # Only a minimal clarify fallback when generation is still unusable.
        recovered = policy_recovery_reply(
            user_text, reason=fail or "empty", language=intel.language
        )
        if recovered:
            return recovered, info_lk

        return EMPTY_GENERATION_FALLBACK, info_lk

    messages = with_runtime_date_context(messages)
    if info.backend == "openai":
        text = chat_via_openai(
            messages,
            model=info.model,
            max_new_tokens=int(kwargs["max_new_tokens"]),
            temperature=float(kwargs["temperature"]),
            top_p=float(kwargs["top_p"]),
        )
        return text, info

    if local_chat is None or not local_loaded:
        raise RuntimeError(
            "No chat backend available. Set OM_MODEL_PROVIDER=om_native with a real "
            "OM-1.0 checkpoint, load a local OM checkpoint (OM_AI_AUTOLOAD=1), or set "
            "OM_AI_OPENAI_API_KEY / OPENAI_API_KEY with OM_AI_CHAT_BACKEND=openai."
        )
    return local_chat(messages, **kwargs), info


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
