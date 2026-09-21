"""STEP 56/68 — Companion Self Improvement (offline learning loop)."""
from .learning_trigger import SelfImprovementRuntime, get_self_improvement
from .improvement_pipeline import ImprovementPipeline, get_improvement_pipeline
from .feedback_engine import FeedbackEngine
from .failure_memory import FailureMemory

__all__ = [
    "SelfImprovementRuntime",
    "get_self_improvement",
    "ImprovementPipeline",
    "get_improvement_pipeline",
    "FeedbackEngine",
    "FailureMemory",
]
