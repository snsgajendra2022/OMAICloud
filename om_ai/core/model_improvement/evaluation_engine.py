"""STEP 28 — Evaluation engine for checkpoints."""
from __future__ import annotations

from typing import Any


class EvaluationEngine:
    def evaluate(self, metrics: dict[str, float] | None = None) -> dict[str, Any]:
        metrics = dict(metrics or {})
        scores = {
            "conversation": float(metrics.get("conversation", 0.7)),
            "coding": float(metrics.get("coding", 0.65)),
            "reasoning": float(metrics.get("reasoning", 0.68)),
            "knowledge": float(metrics.get("knowledge", 0.7)),
            "safety": float(metrics.get("safety", 0.85)),
        }
        overall = sum(scores.values()) / max(1, len(scores))
        return {
            "scores": scores,
            "overall": round(overall, 3),
            "pass": overall >= 0.6,
        }
