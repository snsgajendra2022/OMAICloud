"""Companion personality — tone, affect, and expression."""
from __future__ import annotations

from .affect_analyzer import AffectAnalyzer, AffectState
from .personality_engine import CompanionPersonalityEngine
from .personality_profile import PersonalityProfile

__all__ = [
    "AffectAnalyzer",
    "AffectState",
    "CompanionPersonalityEngine",
    "PersonalityProfile",
]
