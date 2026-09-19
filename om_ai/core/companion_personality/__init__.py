"""Companion personality — tone, affect, and expression."""
from __future__ import annotations

from .affect_analyzer import AffectAnalyzer, AffectState
from .personality_engine import CompanionPersonalityEngine
from .personality_profile import PersonalityProfile
from .voice_presence import (
    detect_speech_locale,
    jarvis_system_hint,
    shape_for_speech,
    social_spoken_reply,
)

__all__ = [
    "AffectAnalyzer",
    "AffectState",
    "CompanionPersonalityEngine",
    "PersonalityProfile",
    "detect_speech_locale",
    "jarvis_system_hint",
    "shape_for_speech",
    "social_spoken_reply",
]
