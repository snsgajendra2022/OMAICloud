"""Conversation feeling — emotional need of the turn (not fake OM feelings)."""
from __future__ import annotations

from typing import Any


class ConversationFeeling:
    def read(
        self,
        *,
        emotion: dict[str, Any] | None = None,
        human: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        emotion = emotion or {}
        human = human or {}
        label = str(emotion.get("emotion") or emotion.get("label") or "neutral")

        if human.get("listen_first") or label in {
            "sad",
            "tired",
            "fatigue",
            "stressed",
            "angry",
            "frustrated",
            "disappointed",
            "masked_stress",
        }:
            return {
                "feeling": label,
                "need": "conversation",
                "response": "supportive",
                "user_is_sharing": True,
            }
        if label in {"happy", "excited"}:
            return {
                "feeling": label,
                "need": "share",
                "response": "match_energy",
                "user_is_sharing": True,
            }
        if label in {"confused"}:
            return {
                "feeling": label,
                "need": "clarity",
                "response": "patient_explain",
                "user_is_sharing": False,
            }
        return {
            "feeling": label,
            "need": "assist",
            "response": "balanced",
            "user_is_sharing": False,
        }
