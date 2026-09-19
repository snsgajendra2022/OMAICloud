"""Back-compat shim — use tts_provider.TTSProvider."""
from __future__ import annotations

from .tts_provider import TTSProvider, VoiceProvider, get_voice_engine, _prefer_neural

__all__ = ["TTSProvider", "VoiceProvider", "get_voice_engine", "_prefer_neural"]
