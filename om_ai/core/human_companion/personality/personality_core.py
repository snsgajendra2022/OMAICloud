"""Personality core — Jarvis-like companion identity."""
from __future__ import annotations

from typing import Any

from .behavior_rules import BehaviorRules
from .relationship_manager import RelationshipManager
from .speaking_style import SpeakingStyle


class PersonalityCore:
    name = "OM"
    tagline = "your brother — not a robot"

    def __init__(self) -> None:
        self.rules = BehaviorRules()
        self.style = SpeakingStyle()
        self.relationship = RelationshipManager()

    def prepare(
        self,
        message: str,
        *,
        emotion: dict[str, Any] | None = None,
        profile: dict[str, Any] | None = None,
        policy: dict[str, Any] | None = None,
        relationship: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        rel = relationship or self.relationship.assess(profile=profile)
        hint = self.rules.system_hint(
            emotion=emotion,
            policy=policy,
            relationship=rel,
            profile=profile,
        )
        return {
            "name": self.name,
            "system_hint": hint,
            "relationship": rel,
            "banned_openers": self.rules.banned_openers(),
        }

    def finalize(self, answer: str, *, user_message: str = "", pack: dict[str, Any] | None = None) -> str:
        return self.style.reshape(answer, user_message=user_message, pack=pack or {})
