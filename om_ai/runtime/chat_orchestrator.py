"""Chat orchestration: template + generation config + quality gate."""
from __future__ import annotations

import logging
import os
import re
from typing import Any

from om_ai.runtime.system_prompts import active_system_prompt

logger = logging.getLogger(__name__)


def _env_float(name: str, default: float) -> float:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def generation_config(**overrides: Any) -> dict[str, Any]:
    """Natural conversational sampling for OM-1.0 chat (env-overridable)."""
    cfg = {
        "temperature": _env_float("OM_CHAT_TEMPERATURE", 0.45),
        "top_p": _env_float("OM_CHAT_TOP_P", 0.9),
        "top_k": _env_int("OM_CHAT_TOP_K", 40),
        "repetition_penalty": _env_float("OM_CHAT_REPETITION_PENALTY", 1.12),
        "max_new_tokens": _env_int("OM_CHAT_MAX_NEW_TOKENS", 96),
        "min_new_tokens": _env_int("OM_CHAT_MIN_NEW_TOKENS", 1),
    }
    for k, v in overrides.items():
        if v is not None:
            cfg[k] = v
    return cfg


def _normalize_messages(messages: list[dict]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for m in messages or []:
        role = str(m.get("role") or "user").strip().lower()
        if role not in {"system", "user", "assistant"}:
            role = "user"
        content = str(m.get("content") or "").strip()
        if content:
            out.append({"role": role, "content": content})
    return out


def build_chat_messages(
    messages: list[dict],
    *,
    compact: bool = False,
    extra_system: str | None = None,
) -> list[dict[str, str]]:
    """Build ChatML-ready messages: system + history (user/assistant turns).

    The tokenizer wraps these as ``<system>…</system><user>…</user><assistant>``.
    """
    msgs = _normalize_messages(messages)
    non_system = [m for m in msgs if m["role"] != "system"]
    # Keep last few turns so OM accounts for the conversation thread.
    if compact and len(non_system) > 8:
        non_system = non_system[-8:]

    system = active_system_prompt(compact=compact)
    if extra_system and extra_system.strip():
        system = f"{system}\n\n{extra_system.strip()}"

    # Prefer a single leading system message.
    return [{"role": "system", "content": system}] + non_system


def policy_recovery_reply(
    user_text: str, *, reason: str = "", language: str = "en"
) -> str | None:
    """Never inject canned chat. The model reply (or EMPTY fallback) is the source of truth."""
    del user_text, reason, language  # kept for call-site compatibility
    return None


def looks_like_assistant_chitchat(text: str | None) -> bool:
    """True when a reply looks like a normal greeting / small-talk assistant turn."""
    s = (text or "").strip()
    if not s or len(s) > 320:
        return False
    if is_low_quality_reply(s):
        return False
    low = s.lower()
    junk = (
        "buy ", "click ", "subscribe", "low fat", "offer or", "win!",
        "membership", "preferred form", "http://", "https://", "www.",
        "cheaper", "performance", "%", "!!", "cold speed", "low k",
    )
    if any(j in low for j in junk):
        return False
    markers = (
        "hi", "hello", "hey", "help", "om ai", "welcome",
        "how can i", "what can i", "good morning", "good evening",
        "nice to meet", "i'm om", "i am om", "how's it", "how are you",
        "नमस्ते", "मदद",
    )
    return any(m in low for m in markers)


def is_low_quality_reply(text: str | None) -> str:
    """Return quality failure reason or empty string if OK."""
    from om_ai.runtime.chat_backend import looks_like_web_spam
    from om_ai.runtime.engine import EMPTY_GENERATION_FALLBACK, is_degenerate_generation, usable_generation_text

    raw = (text or "").strip()
    if not raw or raw == EMPTY_GENERATION_FALLBACK:
        return "empty"
    cleaned = usable_generation_text(raw)
    if not cleaned:
        return "empty"
    if looks_like_web_spam(cleaned):
        return "spam"
    if is_degenerate_generation(cleaned):
        return "degenerate"
    # Catch classic base-model loops: "upgrade upgrade", "membership…"
    low = cleaned.lower()
    if re.search(r"\b(\w+)(?:\s+\1){3,}\b", low):
        return "degenerate"
    if "preferred form" in low and "membership" in low:
        return "spam"
    if "low fat" in low or ("buy ones" in low and "win" in low):
        return "spam"
    return ""
