"""Map internal affect/tone to user-visible expression metadata."""
from __future__ import annotations

from typing import Any

from .affect_analyzer import AffectState


class ExpressionMapper:
    """Public activity/expression labels — not chain-of-thought."""

    ACTIVITY_LABELS = {
        "understand": "Getting the gist",
        "remember": "Recalling context",
        "plan": "Choosing approach",
        "respond": "Composing reply",
        "listen": "Listening",
    }

    def activity(self, stage_key: str) -> str:
        return self.ACTIVITY_LABELS.get(stage_key, "Working on it")

    def expression_meta(
        self,
        affect: AffectState,
        tone: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "user_mood_estimate": affect.label,
            "companion_stance": self._stance(affect, tone),
            "activity_style": tone.get("tone", "friendly"),
        }

    def _stance(self, affect: AffectState, tone: dict[str, Any]) -> str:
        if affect.label in {"frustrated", "concerned"}:
            return "supportive"
        if tone.get("tone") == "professional":
            return "focused"
        if affect.valence > 0.2:
            return "encouraging"
        return "attentive"
