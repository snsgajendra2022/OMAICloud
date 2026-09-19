"""VAD bridge."""
from __future__ import annotations

from typing import Any


class VoiceActivityDetector:
    def status(self) -> dict[str, Any]:
        return {"ready": True, "engine": "voice_intelligence.vad"}
