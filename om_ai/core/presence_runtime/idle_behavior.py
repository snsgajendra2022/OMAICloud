"""Idle / waiting micro-behaviors — keep OM feeling alive without chattering."""
from __future__ import annotations

import time
from typing import Any


class IdleBehavior:
    def __init__(self) -> None:
        self._last_idle_ms = 0.0
        self._idle_count = 0

    def tick(self, *, waiting_since_ms: float) -> dict[str, Any]:
        now = time.time() * 1000
        elapsed = now - waiting_since_ms if waiting_since_ms else 0
        # Soft presence pulse every ~45s of silence — hint only, never speaks alone
        should_pulse = elapsed > 45_000 and (now - self._last_idle_ms) > 45_000
        if should_pulse:
            self._last_idle_ms = now
            self._idle_count += 1
            return {
                "idle_pulse": True,
                "avatar_hint": "soft_breath",
                "glow": 0.4,
                "message": None,  # never auto-speak
            }
        return {
            "idle_pulse": False,
            "avatar_hint": "attentive_rest" if elapsed > 8_000 else "ready",
            "glow": 0.55 if elapsed < 5_000 else 0.35,
            "message": None,
        }
