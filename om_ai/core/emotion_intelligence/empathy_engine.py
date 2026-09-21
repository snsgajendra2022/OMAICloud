"""Empathy engine — what care looks like for this emotion."""
from __future__ import annotations

from typing import Any


class EmpathyEngine:
    _MAP = {
        "frustrated": ("validate_then_help", "That sounds frustrating."),
        "stressed": ("listen_first", "I hear you — that's a lot."),
        "tired": ("gentle_care", "You sound worn out."),
        "sad": ("sit_with", "I'm here with you."),
        "masked_stress": ("soft_door", "Okay — and I'm still here if you want to say more."),
        "happy": ("share_joy", "That's great to hear."),
        "urgent": ("focus_help", "Chalo — jaldi dekhte hain."),
        "neutral": ("steady", ""),
    }

    def guide(self, emotion: str, *, need: str = "") -> dict[str, Any]:
        move, line = self._MAP.get(emotion, self._MAP["neutral"])
        if need == "listen_first":
            move = "listen_first"
        return {
            "empathy_move": move,
            "ack_line": line,
            "avoid": ["lecture", "minimize", "how_can_i_help_you"],
        }
