"""Dialogue style hints for the response layer."""
from __future__ import annotations

from typing import Any

from .personality_profile import PersonalityProfile
from .voice_presence import jarvis_system_hint, shape_for_speech, strip_internal_chrome


class DialogueStyle:
    def system_hint(
        self,
        profile: PersonalityProfile,
        tone: dict[str, Any],
        *,
        conversation_mode: str = "assist",
        voice_mode: bool = True,
    ) -> str:
        if voice_mode:
            return jarvis_system_hint(conversation_mode=conversation_mode)
        return (
            f"You are {profile.name}, {profile.tagline}. "
            f"Conversation mode: {conversation_mode}. "
            f"Tone: {tone.get('tone', 'friendly')}; "
            f"detail: {tone.get('detail', 'balanced')}. "
            "Be natural, supportive, and precise. "
            "Use public-facing clarity — do not expose internal reasoning chains."
        )

    def wrap_answer(
        self,
        answer: str,
        *,
        conversation_mode: str = "assist",
        voice_mode: bool = False,
        user_message: str = "",
    ) -> str:
        text = strip_internal_chrome(answer or "")
        if not text:
            return text
        if voice_mode:
            pack = shape_for_speech(text, user_message=user_message or "")
            spoken = str(pack.get("spoken") or text).strip()
            # Keep answers short for voice companion turns
            sentences = [s.strip() for s in spoken.replace("?", "?|").replace("!", "!|").replace(".", ".|").split("|") if s.strip()]
            if len(sentences) > 3:
                spoken = " ".join(sentences[:3])
            return spoken
        if conversation_mode == "listen" and not text.endswith((".", "!", "?")):
            return text + "."
        return text
