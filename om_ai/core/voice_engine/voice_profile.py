"""Back-compat shim — profiles live in voice_profiles.py."""
from __future__ import annotations

from .voice_profiles import OMVoiceProfile, jarvis_butler_profile

__all__ = ["OMVoiceProfile", "jarvis_butler_profile"]
