"""OM Semantic Intelligence — meaning, intent, goals, context.

Understands what the user meant — not only the literal words.
"""
from __future__ import annotations

from .semantic_engine import SemanticEngine, get_semantic_engine, run_semantic
from .intent_understanding import IntentUnderstanding
from .meaning_representation import MeaningRepresentation, MeaningFrame
from .conversation_state import ConversationState
from .context_reasoner import ContextReasoner
from .ambiguity_resolver import AmbiguityResolver
from .language_understanding import LanguageUnderstanding
from .user_goal_detector import UserGoalDetector

__all__ = [
    "SemanticEngine",
    "get_semantic_engine",
    "run_semantic",
    "IntentUnderstanding",
    "MeaningRepresentation",
    "MeaningFrame",
    "ConversationState",
    "ContextReasoner",
    "AmbiguityResolver",
    "LanguageUnderstanding",
    "UserGoalDetector",
]
