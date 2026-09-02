"""Verifier for Agent Brain replies."""
from __future__ import annotations

import re

from om_ai.runtime.chat_orchestrator import is_low_quality_reply


def verify_reply(text: str | None, *, intent: str = "chat") -> str:
    """Return empty string if OK, else a failure reason."""
    reason = is_low_quality_reply(text)
    if reason:
        return reason
    s = (text or "").strip()
    if not s:
        return "empty"
    if intent in {"coding", "agent"} and len(s.split()) < 4:
        return "too_short"
    if re.search(r"(.)\1{12,}", s):
        return "degenerate"
    return ""


def _feeling_opener(user_text: str) -> str:
    t = (user_text or "").lower()
    if any(w in t for w in ("sad", "upset", "hurt", "lonely", "depress", "cry", "रुला", "दुख")):
        return "I’m really sorry you’re carrying that — thank you for telling me."
    if any(w in t for w in ("stress", "anxious", "worried", "overwhelm", "panic", "टेंशन", "परेशान")):
        return "That sounds heavy. Let’s slow it down together."
    if any(w in t for w in ("happy", "excited", "great", "awesome", "खुश", "मजा")):
        return "I love that energy — let’s build on it."
    if any(w in t for w in ("thank", "thanks", "शुक", "धन्यवाद")):
        return "You’re welcome — I’m glad I could help."
    if any(w in t for w in ("hi", "hello", "hey", "namaste", "नमस्ते", "ram ram", "हेलो")):
        return "Hey — good to see you."
    return "I’m with you."


def compose_fallback(
    *,
    intent: str,
    user_text: str,
    plan_bullets: list[str] | None = None,
    knowledge_snippets: list[str] | None = None,
    grounded_reply: str = "",
) -> str:
    """Reply when the tiny model fails — prefer real datasets / RAG / memory over templates."""
    if grounded_reply.strip():
        return grounded_reply.strip()

    # 1) Dataset brain (ingested instruct / SFT corpora) — real knowledge, not dummy text
    try:
        from om_ai.brain.dataset_engine import grounded_or_none

        hit = grounded_or_none(user_text or "")
        if hit and len(hit) > 60:
            return hit
    except Exception:
        pass

    # 2) RAG snippets already gathered by Agent Brain
    if knowledge_snippets:
        body = "\n\n".join(f"- {s}" for s in knowledge_snippets[:5] if s)
        if body.strip():
            return (
                "**From OM knowledge memory**\n\n"
                f"{body}\n\n"
                f"Ask: { (user_text or '')[:160] }\n\n"
                "I can go deeper — ask a sharper question or say `create python code` / paste an error."
            )

    # 3) Reasoning pipeline (may still pull knowledge)
    if intent in {"coding", "agent", "knowledge", "chat"}:
        try:
            from om_ai.core.reasoning.pipeline import run_reasoning_pipeline

            result = run_reasoning_pipeline(user_text or "", retrieve=True)
            public = str(result.get("answer") or result.get("user_response") or "").strip()
            if public and len(public) > 40:
                return public
            sol = str(result.get("solution") or "").strip()
            if "```" in sol and len(sol) > 80:
                return sol
        except Exception:
            pass

    # 4) Optional static helpers — OFF by default (OM_STATIC_TEMPLATES=1 to enable)
    import os

    if os.environ.get("OM_STATIC_TEMPLATES", "0").strip() in {"1", "true", "yes", "on"}:
        from om_ai.agent.useful_reply import useful_reply_for

        useful = useful_reply_for(user_text, intent=intent)
        if useful:
            return useful

    opener = _feeling_opener(user_text)
    q = (user_text or "").strip()[:180]

    if intent == "greeting":
        qlow = (user_text or "").lower()
        if "how are you" in qlow or "how's it" in qlow:
            return (
                "I’m doing well — thanks for asking.\n\n"
                "I’m **OM AI** on your private stack (model + knowledge brain + memory).\n\n"
                "Ask me anything from your datasets, code, or plans."
            )
        return f"{opener}\n\nI’m **OM AI**. What’s the task?"

    if intent == "identity":
        return (
            "I’m OM AI — local model + dataset brain + memory/RAG in your workspace. "
            "Run `om-ai brain power` to load corpora, then ask real questions."
        )

    if intent == "memory":
        return (
            f"{opener} Memory is on when enabled in settings. "
            "Tell me facts to remember (name, prefs) and I’ll store them."
        )

    if q:
        return (
            f"{opener}\n\n"
            f"**Understood:** {q}\n\n"
            "I don’t have a strong dataset match yet for that. "
            "Load corpora with `om-ai brain power`, or ask with more detail "
            "(code error, file path, or exact goal)."
        )
    return f"{opener} What should we work on?"
