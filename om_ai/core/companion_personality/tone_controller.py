"""Map profile + affect to response tone parameters."""
from __future__ import annotations

from typing import Any

from .affect_analyzer import AffectState
from .personality_profile import PersonalityProfile


class ToneController:
    def resolve(
        self,
        profile: PersonalityProfile,
        affect: AffectState,
    ) -> dict[str, Any]:
        warmth = profile.warmth
        directness = profile.directness
        formality = profile.formality
        if affect.label in {"frustrated", "concerned"}:
            warmth = min(1.0, warmth + 0.12)
            directness = min(1.0, directness + 0.1)
            formality = max(0.2, formality - 0.08)
        elif affect.label in {"positive", "engaged_positive"}:
            warmth = min(1.0, warmth + 0.05)
        tone_name = "friendly"
        if formality > 0.65:
            tone_name = "professional"
        elif profile.playfulness > 0.5 and affect.valence > 0:
            tone_name = "casual"
        detail = "balanced"
        if directness > 0.75:
            detail = "brief"
        elif directness < 0.5:
            detail = "deep"
        return {
            "tone": tone_name,
            "detail": detail,
            "warmth": round(warmth, 3),
            "directness": round(directness, 3),
            "formality": round(formality, 3),
        }
