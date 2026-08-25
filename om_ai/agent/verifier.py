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
    """Structured assistant reply when the tiny model fails (still own stack)."""
    if grounded_reply.strip():
        return grounded_reply.strip()

    opener = _feeling_opener(user_text)
    q = (user_text or "").strip()[:180]

    if intent == "greeting":
        qlow = (user_text or "").lower()
        if "how are you" in qlow or "how's it" in qlow:
            return (
                "👋 I’m doing well — thanks for asking.\n\n"
                "I’m **OM AI**, here with you in your private workspace.\n\n"
                "## I can help with\n"
                "- Code development\n"
                "- Project analysis\n"
                "- AI implementation\n\n"
                "How can I help you today?"
            )
        return (
            f"👋 {opener}\n\n"
            "I’m **OM AI** — here for real conversation, not just answers.\n\n"
            "What’s on your mind?"
        )

    if intent == "identity":
        return (
            f"{opener} I’m OM AI running on OM-1.0 in your private workspace. "
            "I can chat, remember context, use your Knowledge/Memory, and help with plans. "
            "How can I support you right now?"
        )

    if intent == "coding":
        lines = [opener, "", "Here’s a practical plan for that coding task:"]
        for b in plan_bullets or []:
            lines.append(f"- {b}")
        if not plan_bullets:
            lines.append("- Clarify the exact error or goal")
            lines.append("- Locate the relevant files")
            lines.append("- Apply a minimal fix and verify")
        lines.append("")
        lines.append("Share the file path or error log and I’ll go deeper on the next turn.")
        return "\n".join(lines)

    if intent == "agent":
        lines = [opener, "", f"Goal: {q or 'Help with your request'}", "", "Plan:"]
        for b in plan_bullets or ["Understand the need", "Break it into steps", "Deliver a clear answer"]:
            lines.append(f"- {b}")
        if knowledge_snippets:
            lines.append("")
            lines.append("From knowledge:")
            for s in knowledge_snippets[:2]:
                lines.append(f"- {s[:160]}")
        return "\n".join(lines)

    if intent == "knowledge" and knowledge_snippets:
        return (
            f"{opener}\n\nBased on what I have in knowledge:\n"
            + "\n".join(f"- {s[:200]}" for s in knowledge_snippets[:3])
        )

    if intent == "memory":
        return (
            f"{opener} I’ll keep what matters from our chats when Memory is enabled. "
            "Tell me what you’d like me to remember."
        )

    # Default chat — human, context-aware bridge
    if q:
        return (
            f"{opener} I hear you about “{q}”. "
            "Tell me a bit more about what you need — a short answer, steps, or just someone to think with — "
            "and I’ll meet you there."
        )
    return f"{opener} What would you like to talk about?"
