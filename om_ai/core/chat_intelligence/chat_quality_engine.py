"""Chat quality engine — final answer quality gate."""
from __future__ import annotations

from typing import Any


class ChatQualityEngine:
    """Aggregate quality decision for the final chat response."""

    def evaluate(
        self,
        answer: str,
        *,
        optimizer_report: dict[str, Any] | None = None,
        confidence: dict[str, Any] | None = None,
        intent: str = "",
    ) -> dict[str, Any]:
        text = (answer or "").strip()
        optimizer_report = dict(optimizer_report or {})
        confidence = dict(confidence or {})

        issues: list[str] = list(optimizer_report.get("issues") or [])
        score = float(optimizer_report.get("score") or (0.9 if text else 0.0))
        conf = float(confidence.get("confidence") or 0.5)

        if not text:
            issues.append("empty")
            score = 0.0
        if conf < 0.4:
            issues.append("low_confidence")

        approved = bool(text) and score >= 0.5 and "gibberish" not in issues
        return {
            "approved": approved,
            "score": round(score, 3),
            "confidence": conf,
            "issues": issues,
            "intent": intent,
        }
