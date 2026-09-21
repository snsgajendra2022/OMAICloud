"""Wellbeing engine — conversational signals only (STEP 55)."""
from __future__ import annotations

from typing import Any

from .fatigue_detector import FatigueDetector
from .stress_signal import StressSignal
from .wellbeing_context import WellbeingContext
from .wellbeing_response import WellbeingResponse


class WellbeingEngine:
    def __init__(self) -> None:
        self.fatigue = FatigueDetector()
        self.stress = StressSignal()
        self.context = WellbeingContext()
        self.response = WellbeingResponse()

    def observe(self, message: str, *, locale: str = "en") -> dict[str, Any]:
        fat = self.fatigue.detect(message)
        stress = self.stress.detect(message)

        # Prefer higher-confidence hit
        hit = fat if fat.get("hit") and float(fat.get("confidence") or 0) >= float(
            stress.get("confidence") or 0
        ) else stress if stress.get("hit") else fat if fat.get("hit") else {}

        signal = hit.get("signal")
        confidence = float(hit.get("confidence") or 0.0)
        care = self.response.build(str(signal) if signal else None, locale=locale)

        pack = {
            "has_signal": bool(signal),
            "active": bool(signal),
            "signal": signal,
            "primary": signal,
            "confidence": confidence,
            "label": hit.get("label"),
            "response_style": care.get("response_style") or "supportive",
            "care_line": care.get("care_line") or "",
            "diagnose": False,
            "disclaimer": care.get("disclaimer"),
            "system_hint": care.get("system_hint") or "",
            "context": self.context.summary(),
        }
        self.context.push(pack)
        return pack
