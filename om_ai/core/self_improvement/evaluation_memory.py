"""Evaluation memory for offline scoring."""
from __future__ import annotations

import time
from typing import Any


class EvaluationMemory:
    def __init__(self) -> None:
        self.scores: list[dict[str, Any]] = []

    def store(self, *, metric: str, value: float, note: str = "") -> None:
        self.scores.append(
            {"ts": time.time(), "metric": metric, "value": value, "note": note[:200]}
        )
        self.scores = self.scores[-300:]

    def summary(self) -> dict[str, Any]:
        if not self.scores:
            return {"count": 0, "avg": None}
        vals = [float(s["value"]) for s in self.scores[-50:]]
        return {"count": len(self.scores), "avg": sum(vals) / max(1, len(vals))}
