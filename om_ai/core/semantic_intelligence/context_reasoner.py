"""Context reasoner — use history + state to interpret this turn."""
from __future__ import annotations

import re
from typing import Any


class ContextReasoner:
    """Resolve pronouns / short follow-ups against conversation state."""

    def reason(
        self,
        text: str,
        *,
        state: dict[str, Any] | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        state = state or {}
        hist = history or []
        low = (text or "").lower().strip()
        topic = str(state.get("topic") or "general")
        entities = list(state.get("entities") or [])

        is_followup = bool(
            re.search(r"(?i)\b(it|that|this|us[ei]|wahi|usko|uska|continue|and then)\b", low)
            or len(low.split()) <= 3
        )

        referent = None
        if is_followup:
            if entities:
                referent = entities[-1]
            else:
                for h in reversed(hist[-6:]):
                    content = str(h.get("content") or h.get("text") or "")
                    if content and h.get("role") in {"user", "assistant", None}:
                        referent = content[:80]
                        break

        enriched = text
        if is_followup and referent and len(low.split()) <= 5:
            enriched = f"{text} (about: {referent})"

        return {
            "topic": topic,
            "is_followup": is_followup,
            "referent": referent,
            "enriched_text": enriched,
            "active_entities": entities[-5:],
            "open_question": state.get("open_question"),
            "hint": (
                f"Continue the thread about {topic}."
                if is_followup and topic != "general"
                else ""
            ),
        }
