"""Back-compat shim — use streaming_voice.StreamingVoice."""
from __future__ import annotations

from .streaming_voice import SpeechStream, StreamingVoice

__all__ = ["StreamingVoice", "SpeechStream"]
