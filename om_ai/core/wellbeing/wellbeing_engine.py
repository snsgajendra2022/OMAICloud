"""Wellbeing engine — notice strain; never diagnose."""
from __future__ import annotations

from typing import Any

from .signal_detector import SignalDetector
from .supportive_response import SupportiveResponse


class WellbeingEngine:
    def __init__(self) -> None:
        self.signals = SignalDetector()
        self.support = SupportiveResponse()

    def observe(self, message: str, *, locale: str = "en") -> dict[str, Any]:
        detected = self.signals.detect(message)
        care = self.support.suggest(detected, locale=locale)
        return {
            **detected,
            **care,
            "active": bool(detected.get("has_signal")),
        }
