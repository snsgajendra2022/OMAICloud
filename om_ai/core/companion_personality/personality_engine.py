"""Companion personality engine — coordinates profile, affect, and tone."""
from __future__ import annotations

from typing import Any

from .affect_analyzer import AffectAnalyzer, AffectState
from .dialogue_style import DialogueStyle
from .expression_mapper import ExpressionMapper
from .personality_profile import PersonalityProfile
from .relationship_context import RelationshipContext
from .tone_controller import ToneController


class CompanionPersonalityEngine:
    def __init__(self) -> None:
        self.affect = AffectAnalyzer()
        self.tone = ToneController()
        self.style = DialogueStyle()
        self.relationship = RelationshipContext()
        self.expression = ExpressionMapper()

    def prepare(
        self,
        message: str,
        *,
        intent: str = "",
        intent_confidence: float = 0.5,
        history: list[dict[str, Any]] | None = None,
        preferences: dict[str, str] | None = None,
        conversation_mode: str = "assist",
    ) -> dict[str, Any]:
        profile = PersonalityProfile.from_prefs(preferences)
        affect: AffectState = self.affect.analyze(
            message,
            intent=intent,
            intent_confidence=intent_confidence,
            history=history,
        )
        tone = self.tone.resolve(profile, affect)
        rel = self.relationship.assess(history=history)
        hint = self.style.system_hint(
            profile, tone, conversation_mode=conversation_mode
        )
        return {
            "profile": profile.to_dict(),
            "affect": affect.to_dict(),
            "tone": tone,
            "relationship": rel,
            "system_hint": hint,
            "expression": self.expression.expression_meta(affect, tone),
        }

    def finalize(
        self,
        answer: str,
        pack: dict[str, Any],
        *,
        conversation_mode: str = "assist",
    ) -> str:
        return self.style.wrap_answer(
            answer, conversation_mode=conversation_mode or pack.get("conversation_mode", "assist")
        )
