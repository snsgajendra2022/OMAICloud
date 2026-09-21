"""Supportive wellbeing wording — care, not diagnosis."""
from __future__ import annotations

from typing import Any


class SupportiveResponse:
    _LINES = {
        "sleep_debt": (
            "That sounds exhausting. Lack of sleep for several days can affect how you feel and work. "
            "If possible, try to get some rest. How are you feeling today?"
        ),
        "fatigue": (
            "You sound worn out. A short pause can help more than pushing through. "
            "How are you holding up?"
        ),
        "work_overload": (
            "That load sounds heavy. Maybe we pick one priority and park the rest for a bit. "
            "What's the one thing that matters most right now?"
        ),
        "stress_load": (
            "I can hear the stress in that. I'm here with you — want to talk it through or take one small step?"
        ),
        "low_mood": (
            "I'm glad you told me. You don't have to carry that alone. "
            "I'm here to listen — what's been weighing on you?"
        ),
    }

    def suggest(self, signals: dict[str, Any], *, locale: str = "en") -> dict[str, Any]:
        primary = signals.get("primary")
        line = self._LINES.get(str(primary or ""), "")
        if locale == "hi" and primary == "sleep_debt":
            line = (
                "Sir, yeh sunke thakaan lagti hai. Kai din kam neend se kaam aur mood dono pe asar padta hai. "
                "Agar ho sake thoda rest lijiye — aaj aap kaise feel kar rahe ho?"
            )
        return {
            "care_line": line,
            "diagnose": False,
            "disclaimer": "Companion support only — not medical advice.",
            "system_hint": (
                "Notice wellbeing strain gently. Do not diagnose. "
                "Offer rest/support and one caring question. Never prescribe medication."
                + (f" Suggested care: {line}" if line else "")
            ),
        }
