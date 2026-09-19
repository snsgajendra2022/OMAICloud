"""Breathing markers for natural delivery."""
from __future__ import annotations

from typing import Any


class BreathingEngine:
    def markers(self, text: str) -> dict[str, Any]:
        commas = (text or "").count(",")
        stops = sum((text or "").count(c) for c in ".!?।")
        return {"comma_pauses": commas, "sentence_pauses": stops, "breath_points": commas + stops}
