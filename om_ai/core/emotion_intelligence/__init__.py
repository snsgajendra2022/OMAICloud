"""Emotion intelligence — detect, track mood, choose empathic response style."""
from __future__ import annotations

from .emotion_engine import EmotionEngine
from .emotion_detector import EmotionDetector
from .emotion_state import EmotionState
from .empathy_engine import EmpathyEngine
from .tone_controller import ToneController

__all__ = [
    "EmotionEngine",
    "EmotionDetector",
    "EmotionState",
    "EmpathyEngine",
    "ToneController",
]
