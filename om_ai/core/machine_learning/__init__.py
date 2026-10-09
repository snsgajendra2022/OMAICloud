"""OM AI's controlled machine-learning lifecycle.

This package prepares/version datasets, records feedback, evaluates candidate
responses, and coordinates explicit training adapters. It does not silently
retrain or replace production weights from live conversations.
"""
from .learning_config import LearningConfig
from .learning_engine import LearningEngine, LearningResult

__all__ = ["LearningConfig", "LearningEngine", "LearningResult"]
