"""Confidence scoring for chat answers."""
from __future__ import annotations

from typing import Any


class ConfidenceEngine:
    """Estimate confidence that the answer solves the user ask."""

    def score(
        self,
        *,
        intent: str = "",
        quality: dict[str, Any] | None = None,
        solution: dict[str, Any] | None = None,
        used_model: bool = False,
        corrected: bool = False,
    ) -> dict[str, Any]:
        quality = dict(quality or {})
        solution = dict(solution or {})
        base = 0.55

        if intent in {"greeting", "morning", "evening", "afternoon", "identity", "thanks", "goodbye"}:
            base = 0.95
        elif solution.get("solved") and solution.get("complete"):
            base = 0.88
        elif solution.get("solved"):
            base = 0.78
        elif used_model:
            base = 0.62

        qscore = float(quality.get("score") or 0.5)
        conf = (base * 0.65) + (qscore * 0.35)
        if corrected:
            conf = max(conf, 0.7)
        if quality.get("ok") is False:
            conf = min(conf, 0.45)

        conf = max(0.05, min(0.99, conf))
        return {
            "confidence": round(conf, 3),
            "level": "high" if conf >= 0.8 else ("medium" if conf >= 0.6 else "low"),
        }
