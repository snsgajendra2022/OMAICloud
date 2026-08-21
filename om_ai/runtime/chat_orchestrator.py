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
    """ChatGPT-style sampling defaults for OM-1.0 chat (env-overridable)."""
    cfg = {
        "temperature": _env_float("OM_CHAT_TEMPERATURE", 0.7),
        "top_p": _env_float("OM_CHAT_TOP_P", 0.9),
        "top_k": _env_int("OM_CHAT_TOP_K", 50),
        "repetition_penalty": _env_float("OM_CHAT_REPETITION_PENALTY", 1.15),
        "max_new_tokens": _env_int("OM_CHAT_MAX_NEW_TOKENS", 256),
        "min_new_tokens": _env_int("OM_CHAT_MIN_NEW_TOKENS", 4),
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
    # Keep last few turns to reduce noise for tiny context windows.
    if compact and len(non_system) > 4:
        non_system = non_system[-4:]

    system = active_system_prompt(compact=compact)
    if extra_system and extra_system.strip():
        system = f"{system}\n\n{extra_system.strip()}"

    # Prefer a single leading system message.
    return [{"role": "system", "content": system}] + non_system


_GREETING_REPLY = (
    "Hi! I'm OM AI. How can I help you today?"
)
_OM_SELF_REPLY = (
    "I'm OM AI, powered by the OM-1.0 native model running locally on your machine. "
    "I can chat, remember our conversation history in this workspace, and help with "
    "writing, explaining, and brainstorming. What would you like to do?"
)
_CLARIFY_REPLY = (
    "I didn't catch a clear answer there. Could you rephrase that in one short sentence?"
)


def policy_recovery_reply(
    user_text: str, *, reason: str = "", language: str = "en"
) -> str | None:
    """Safe assistant reply when the base model fails quality gates.

    This is an orchestration safety net for undertrained local checkpoints —
    not a replacement for SFT. Only used after degenerate / spam generations.
    """
    from om_ai.live_knowledge.freshness import is_greeting_like, is_om_self_query

    if is_greeting_like(user_text):
        if language in {"hi", "hi-Latn"}:
            return "Namaste! Main OM AI hoon. Aaj main aapki kaise madad kar sakta hoon?"
        return _GREETING_REPLY
    if is_om_self_query(user_text):
        if language in {"hi", "hi-Latn"}:
            return (
                "Main OM AI hoon — aapke machine par chalne wala OM-1.0 native model. "
                "Main chat, memory, aur writing/brainstorming mein madad karta hoon. "
                "Aap kya karna chahenge?"
            )
        return _OM_SELF_REPLY
    if reason in {"degenerate", "spam", "empty"}:
        if language in {"hi", "hi-Latn"}:
            return "Mujhe clear jawab nahi mila. Kya aap ek short sentence mein dobara bata sakte hain?"
        return _CLARIFY_REPLY
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
