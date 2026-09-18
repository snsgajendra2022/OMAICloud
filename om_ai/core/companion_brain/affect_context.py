"""Bridge affect into companion brain context."""
from __future__ import annotations

from typing import Any

from om_ai.core.companion_personality import CompanionPersonalityEngine


class AffectContext:
    def __init__(self) -> None:
        self._personality = CompanionPersonalityEngine()

    def build(
        self,
        message: str,
        semantic: dict[str, Any],
        *,
        history: list[dict[str, Any]] | None = None,
        preferences: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self._personality.prepare(
            message,
            intent=str(semantic.get("intent") or ""),
            intent_confidence=float(semantic.get("confidence") or 0.5),
            history=history,
            preferences=preferences,
            conversation_mode=str(semantic.get("conversation_mode") or "assist"),
        )
