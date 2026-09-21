"""Predict whether the user is about to keep talking."""
from __future__ import annotations

from typing import Any


class TurnPrediction:
    def predict(self, meaning: dict[str, Any] | None = None) -> dict[str, Any]:
        m = meaning or {}
        continuing = bool(m.get("user_continuing") or m.get("needs_listening"))
        return {
            "user_likely_continues": continuing,
            "om_should_hold": continuing,
            "confidence": float((m.get("completion") or {}).get("confidence") or 0.6),
        }
