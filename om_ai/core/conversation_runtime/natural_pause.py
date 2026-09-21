"""Natural pause detection — when user likely finished speaking."""
from __future__ import annotations

import time
from typing import Any


class NaturalPause:
    def __init__(self, silence_ms: float = 650) -> None:
        self.silence_ms = silence_ms
        self._last_audio_ms = 0.0

    def on_audio(self) -> None:
        self._last_audio_ms = time.time() * 1000

    def ready_to_commit(self, *, has_partial: bool) -> dict[str, Any]:
        if not has_partial:
            return {"commit": False, "reason": "no_speech"}
        gap = time.time() * 1000 - self._last_audio_ms if self._last_audio_ms else 0
        if gap >= self.silence_ms:
            return {"commit": True, "silence_ms": gap, "reason": "natural_pause"}
        return {"commit": False, "silence_ms": gap, "reason": "still_speaking"}
