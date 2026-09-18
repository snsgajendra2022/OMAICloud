"""STEP 28 — Checkpoint selector."""
from __future__ import annotations

from typing import Any


class CheckpointSelector:
    def select(self, candidates: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        cands = list(candidates or [])
        if not cands:
            return {
                "selected": "om-1.0-current",
                "score": 0.7,
                "reason": "default_active_checkpoint",
            }
        best = max(cands, key=lambda c: float(c.get("score") or 0))
        return {
            "selected": best.get("name") or best.get("path") or "unknown",
            "score": float(best.get("score") or 0),
            "reason": "highest_eval_score",
            "candidate": best,
        }
