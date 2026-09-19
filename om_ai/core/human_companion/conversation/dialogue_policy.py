"""Dialogue policy for human companion turns."""
from __future__ import annotations

from typing import Any


class DialoguePolicy:
    def decide(
        self,
        *,
        semantic: dict[str, Any] | None = None,
        emotion: dict[str, Any] | None = None,
        followup: dict[str, Any] | None = None,
        is_action: bool = False,
    ) -> dict[str, Any]:
        sem = semantic or {}
        emo = (emotion or {}).get("label") or "neutral"
        mode = sem.get("conversation_mode") or "assist"
        if is_action:
            return {"policy": "execute_then_confirm", "max_sentences": 2, "ask_questions": False}
        if emo in {"frustration", "stress", "urgency", "sad"}:
            return {"policy": "empathic_assist", "max_sentences": 3, "ask_questions": False, "tone": "soft"}
        if emo in {"happy", "excitement"}:
            return {"policy": "warm_assist", "max_sentences": 3, "ask_questions": False, "tone": "warm"}
        if followup and followup.get("is_reference"):
            return {"policy": "thread_continuity", "max_sentences": 4, "ask_questions": False}
        if mode == "social":
            return {"policy": "social_brief", "max_sentences": 2, "ask_questions": False}
        return {"policy": "balanced_assist", "max_sentences": 3, "ask_questions": False, "tone": "calm"}
