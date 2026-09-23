"""Empathy engine — care without fake human feelings.

OM does not pretend to feel. OM understands and responds with care.
"""
from __future__ import annotations

from typing import Any


class EmpathyEngine:
    _MAP = {
        "disappointed": ("encourage", "That sounds disappointing.", "encouraging"),
        "frustrated": ("validate_then_help", "That sounds frustrating.", "steady"),
        "stressed": ("listen_first", "I hear you — that's a lot.", "supportive"),
        "tired": ("gentle_care", "You sound worn out.", "gentle"),
        "fatigue": ("gentle_care", "You sound worn out.", "gentle"),
        "sad": ("sit_with", "I'm here with you.", "soft"),
        "angry": ("solidarity", "I get why that would make you angry.", "steady"),
        "masked_stress": ("soft_door", "Okay — and I'm still here if you want to say more.", "soft"),
        "happy": ("share_joy", "That's great to hear.", "warm"),
        "excited": ("share_joy", "Love that energy.", "warm"),
        "urgent": ("focus_help", "Alright — let's look at this quickly.", "focused"),
        "confused": ("clarify", "Let's slow it down and make this clear.", "patient"),
        "romantic": ("respectful_care", "I've got your back with care.", "warm"),
        "neutral": ("steady", "", "balanced"),
    }

    def guide(self, emotion: str, *, need: str = "") -> dict[str, Any]:
        move, line, response = self._MAP.get(emotion, self._MAP["neutral"])
        if need in {"listen_first", "conversation", "support_and_listen"}:
            move = "listen_first"
            response = "supportive"
        return {
            "empathy_move": move,
            "ack_line": line,
            "response": response,
            "avoid": ["lecture", "minimize", "how_can_i_help_you", "fake_feelings"],
            # Honesty: understanding ≠ having human feelings
            "om_claims_feelings": False,
            "guidance": (
                "Acknowledge the user's state. Stay warm and honest. "
                "Do not say you feel human emotions. Do not jump to solutions if they are sharing."
            ),
        }
