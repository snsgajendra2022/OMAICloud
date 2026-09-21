"""Supportive wellbeing wording — care, never diagnosis."""
from __future__ import annotations

from typing import Any


class WellbeingResponse:
    _LINES = {
        "sleep_deprivation": (
            "That sounds exhausting. Your sleep seems very limited recently. "
            "Try to take some rest if possible. How are you feeling today?"
        ),
        "fatigue": (
            "You sound really tired today. "
            "Was it because of work, stress, or something else? "
            "If you have been pushing yourself too much, take a small break also."
        ),
        "stress_load": (
            "I can hear the stress in that. I'm here with you — "
            "want to talk it through or take one small step?"
        ),
        "work_overload": (
            "That load sounds heavy. Maybe we pick one priority and park the rest for a bit. "
            "What's the one thing that matters most right now?"
        ),
        "low_mood": (
            "I'm glad you told me. You don't have to carry that alone. "
            "I'm here to listen — what's been weighing on you?"
        ),
    }

    def build(self, signal: str | None, *, locale: str = "en") -> dict[str, Any]:
        key = str(signal or "")
        line = self._LINES.get(key, "")
        if locale == "hi" and key == "sleep_deprivation":
            line = (
                "Sir, yeh sunke thakaan lagti hai. Neend kam rehne se mood aur kaam dono pe asar padta hai. "
                "Agar ho sake thoda rest lijiye — aaj aap kaise feel kar rahe ho?"
            )
        elif locale == "hi" and key == "fatigue":
            line = (
                "Aaj aap bilkul thake hue lag rahe ho. "
                "Kaam, stress, ya kuch aur? Agar zyada push kiya hai to chhota sa break bhi lo."
            )
        return {
            "care_line": line,
            "response_style": "supportive" if line else "balanced",
            "diagnose": False,
            "disclaimer": "Companion support only — not medical advice.",
            "system_hint": (
                "Notice wellbeing strain gently. Do NOT diagnose or prescribe. "
                "Offer rest/support and one caring question."
                + (f" Suggested care: {line}" if line else "")
            ),
        }
