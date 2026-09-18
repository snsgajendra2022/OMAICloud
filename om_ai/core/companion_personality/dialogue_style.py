"""Dialogue style hints for the response layer."""
from __future__ import annotations

from typing import Any

from .personality_profile import PersonalityProfile


class DialogueStyle:
    def system_hint(
        self,
        profile: PersonalityProfile,
        tone: dict[str, Any],
        *,
        conversation_mode: str = "assist",
    ) -> str:
        return (
            f"You are {profile.name}, {profile.tagline}. "
            f"Conversation mode: {conversation_mode}. "
            f"Tone: {tone.get('tone', 'friendly')}; "
            f"detail: {tone.get('detail', 'balanced')}. "
            "Be natural, supportive, and precise. "
            "Use public-facing clarity — do not expose internal reasoning chains."
        )

    def wrap_answer(self, answer: str, *, conversation_mode: str = "assist") -> str:
        text = (answer or "").strip()
        if not text:
            return text
        if conversation_mode == "listen" and not text.endswith((".", "!", "?")):
            return text + "."
        return text
