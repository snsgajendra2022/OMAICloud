"""Back-compat shim — use voice_model.VoiceModel."""
from __future__ import annotations

from .voice_model import NeuralTTS, VoiceModel

__all__ = ["NeuralTTS", "VoiceModel"]
