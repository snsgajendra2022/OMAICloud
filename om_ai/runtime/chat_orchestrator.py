"""Chat orchestration: template + generation config + quality gate."""
from __future__ import annotations

import logging
import os
import re
from typing import Any

from om_ai.runtime.system_prompts import active_system_prompt

logger = logging.getLogger(__name__)


def run_cognitive_brain(
    question: str,
    *,
    knowledge: Any = None,
    native_chat: Any = None,
) -> dict[str, Any]:
    """Run OMCognitiveBrain.process with a real user question (never at import)."""
    from om_ai.core.cognitive.brain_pipeline import OMCognitiveBrain

    return OMCognitiveBrain().process(
        question,
        knowledge=knowledge,
        native_chat=native_chat,
    )


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
    """ChatGPT-style sampling for OM-1.0 chat (env-overridable).

    Defaults: temperature 0.7, top_p 0.9, repetition_penalty 1.2, no_repeat_ngram 3.
    """
    cfg = {
        "temperature": _env_float("OM_CHAT_TEMPERATURE", 0.7),
        "top_p": _env_float("OM_CHAT_TOP_P", 0.9),
        "top_k": _env_int("OM_CHAT_TOP_K", 50),
        "repetition_penalty": _env_float("OM_CHAT_REPETITION_PENALTY", 1.2),
        "max_new_tokens": _env_int("OM_CHAT_MAX_NEW_TOKENS", 96),
        "min_new_tokens": _env_int("OM_CHAT_MIN_NEW_TOKENS", 1),
        "no_repeat_ngram_size": _env_int("OM_CHAT_NO_REPEAT_NGRAM", 3),
        "repetition_window": _env_int("OM_CHAT_REPETITION_WINDOW", 128),
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
    if is_nonsensical_smalltalk(s):
        return False
    low = s.lower()
    junk = (
        "buy ", "click ", "subscribe", "low fat", "offer or", "win!",
        "membership", "preferred form", "http://", "https://", "www.",
        "cheaper", "performance", "%", "!!", "cold speed", "low k",
        "car sim",
    )
    if any(j in low for j in junk):
        return False
    markers = (
        "hi", "hello", "hey", "help", "om ai", "i'm om", "i am om", "welcome",
        "how can i", "what can i", "good morning", "good evening",
        "nice to meet", "how's it", "how are you", "doing well", "i'm here",
        "i am here", "glad", "नमस्ते", "मदद",
    )
    return any(m in low for m in markers)


def is_garbled_generation(text: str | None) -> bool:
    """Detect tiny-model nonsense (mixed-script spam, random proper nouns, fragment soup)."""
    s = (text or "").strip()
    if not s:
        return True
    try:
        from om_ai.runtime.public_reply import looks_like_genesis_template

        if looks_like_genesis_template(s):
            return True
    except Exception:
        pass
    has_dev = bool(re.search(r"[\u0900-\u097F]", s))
    words = re.findall(r"[A-Za-z']+", s)
    low = s.lower()
    uniq = len({w.lower() for w in words}) / max(len(words), 1) if words else 1.0
    # Classic derail phrases seen from undertrained OM-1.0 chat
    if any(
        p in low
        for p in (
            "prime minister",
            "powered byhi",
            "dail name",
            "car sim",
            "cold speed",
            "preferred form",
            "low fat",
            "distrable",
            "powereign",
            "sticondoncas",
            "parvestivle",
        )
    ):
        return True
    # High rate of weird long tokens without vowels patterns / misspell soup
    if len(words) >= 8:
        weird = 0
        for w in words:
            if len(w) >= 7:
                vowels = sum(1 for c in w.lower() if c in "aeiou")
                if vowels <= 1 or re.search(r"[A-Z]{2,}[a-z]+[A-Z]", w):
                    weird += 1
        if weird / max(len(words), 1) >= 0.2:
            return True
        if uniq > 0.9 and s.count(".") <= 1 and "```" not in s and "http" not in low:
            return True
    # Mixed Devanagari + English fragment soup (not intentional bilingual help)
    if has_dev and len(words) >= 6:
        intentional = any(
            x in s.lower() or x in s
            for x in ("namaste", "नमस्ते", "धन्यवाद", "हिंदी", "hindi", "english meaning")
        )
        short = sum(1 for w in words if len(w) <= 2)
        weird = sum(1 for w in words if re.search(r"[A-Z]{2,}", w) and w.lower() not in {"om", "ai", "api", "ui"})
        if not intentional and (short >= 3 or "syntax" in low or weird >= 2):
            return True
    # High comma / fragment density without clear sentence structure
    if len(words) >= 10 and s.count(",") >= 4 and s.count(".") == 0 and "http" not in low:
        return True
    # Short nonsense / near-echo of the user question
    if 1 <= len(words) <= 8 and s.count(".") == 0 and "```" not in s and "http" not in low:
        if not any(
            k in low
            for k in (
                "react",
                "python",
                "hello",
                "help",
                "dashboard",
                "install",
                "npm",
                "i’m om",
                "i am om",
                "couldn’t",
                "please",
            )
        ):
            return True
    return False


def is_nonsensical_smalltalk(text: str | None) -> bool:
    """Detect undertrained greeting derails (e.g. 'Hello! I’m on Car sim…')."""
    s = (text or "").strip()
    if not s:
        return True
    if is_garbled_generation(s):
        return True
    low = s.lower()
    if any(
        p in low
        for p in (
            "car sim",
            "keeping us on",
            "cold speed",
            "low k",
            "preferred form",
        )
    ):
        return True
    words = re.findall(r"[A-Za-z']+", s)
    if len(words) >= 6 and s.count(",") >= max(3, len(words) // 3):
        return True
    # Starts like a greeting then drifts into unrelated fragments
    if re.match(r"^(hi|hello|hey)\b", low):
        rest = low.split(None, 1)[1] if " " in low else ""
        if rest and not any(
            k in rest
            for k in (
                "om",
                "well",
                "good",
                "fine",
                "here",
                "help",
                "assist",
                "mind",
                "day",
                "thanks",
                "welcome",
                "glad",
                "doing",
            )
        ):
            if len(words) >= 6:
                return True
    return False


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
    if is_garbled_generation(cleaned):
        return "garbled"
    if is_nonsensical_smalltalk(cleaned):
        return "nonsensical"
    # Catch classic base-model loops: "upgrade upgrade", "membership…"
    low = cleaned.lower()
    if re.search(r"\b(\w+)(?:\s+\1){3,}\b", low):
        return "degenerate"
    if "preferred form" in low and "membership" in low:
        return "spam"
    if "low fat" in low or ("buy ones" in low and "win" in low):
        return "spam"
    return ""
