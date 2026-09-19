"""Back-compat shim — use voice_cloner.VoiceCloner."""
from __future__ import annotations

from .voice_cloner import VoiceCloneAdapter, VoiceCloner

__all__ = ["VoiceCloner", "VoiceCloneAdapter"]
