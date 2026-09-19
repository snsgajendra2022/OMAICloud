"""Streaming TTS bridge."""
from __future__ import annotations

from typing import Any


class StreamingTTS:
    def status(self) -> dict[str, Any]:
        return {"ready": True, "provider": "macos_aman_or_elevenlabs"}
