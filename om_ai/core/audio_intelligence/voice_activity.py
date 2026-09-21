"""Voice activity — start / stop / still speaking."""
from __future__ import annotations

import time
from typing import Any


class VoiceActivity:
    def __init__(self, *, hangover_ms: float = 450) -> None:
        self.hangover_ms = hangover_ms
        self._speaking = False
        self._last_voice_ms = 0.0
        self._started_ms = 0.0

    def update(self, *, energy: float = 0.0, speech_prob: float = 0.0) -> dict[str, Any]:
        now = time.time() * 1000
        active = float(energy) >= 0.03 or float(speech_prob) >= 0.4
        if active:
            if not self._speaking:
                self._speaking = True
                self._started_ms = now
            self._last_voice_ms = now
            return {
                "speaking": True,
                "event": "continue" if now - self._started_ms > 80 else "start",
                "silence_ms": 0.0,
            }
        silence = now - self._last_voice_ms if self._last_voice_ms else 0.0
        if self._speaking and silence >= self.hangover_ms:
            self._speaking = False
            return {"speaking": False, "event": "stop", "silence_ms": silence}
        return {
            "speaking": self._speaking,
            "event": "pause" if self._speaking else "idle",
            "silence_ms": silence,
        }
