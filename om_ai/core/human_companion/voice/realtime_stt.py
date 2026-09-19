"""Realtime STT bridge."""
from __future__ import annotations

from typing import Any


class RealtimeSTT:
    def status(self) -> dict[str, Any]:
        return {"ready": True, "primary": "browser_web_speech", "secondary": "voice_intelligence.streaming_stt"}
