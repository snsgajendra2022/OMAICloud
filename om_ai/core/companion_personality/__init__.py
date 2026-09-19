"""Companion personality — tone, affect, and expression."""
from __future__ import annotations

from .affect_analyzer import AffectAnalyzer, AffectState
from .personality_engine import CompanionPersonalityEngine
from .personality_profile import PersonalityProfile
from .voice_presence import (
    VoicePresenceEngine,
    detect_speech_locale,
    get_voice_presence,
    jarvis_system_hint,
    shape_for_speech,
    social_spoken_reply,
)

__all__ = [
    "AffectAnalyzer",
    "AffectState",
    "CompanionPersonalityEngine",
    "PersonalityProfile",
    "VoicePresenceEngine",
    "detect_speech_locale",
    "get_voice_presence",
    "jarvis_system_hint",
    "shape_for_speech",
    "social_spoken_reply",
]
