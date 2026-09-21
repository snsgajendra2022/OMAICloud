"""Empathy-first plan when conversation_need asks for care."""
from __future__ import annotations

from typing import Any


class EmpathyPlanner:
    def plan(self, emotion: dict[str, Any] | None = None) -> dict[str, Any]:
        emotion = emotion or {}
        label = str(emotion.get("emotion") or "neutral")
        need = str(emotion.get("conversation_need") or emotion.get("need") or "steady")
        if need in {"listen_first", "support_and_listen"} or label in {
            "sad",
            "stressed",
            "frustrated",
            "tired",
            "masked_stress",
        }:
            return {
                "lead_with": "validate",
                "then": "one_open_question",
                "avoid": ["how_can_i_help", "lecture", "instant_fix"],
                "max_sentences": 2,
            }
        if label in {"happy", "excited"}:
            return {
                "lead_with": "share",
                "then": "continue",
                "avoid": ["dampen"],
                "max_sentences": 2,
            }
        return {
            "lead_with": "acknowledge",
            "then": "help",
            "avoid": ["how_can_i_help"],
            "max_sentences": 3,
        }
