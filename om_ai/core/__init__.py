"""OM AI Foundation — core intelligence modules (additive, non-breaking)."""
from __future__ import annotations

from om_ai.core.reasoning import (
    IntentAnalyzer,
    PlanningEngine,
    ReflectionEngine,
    SolutionGenerator,
    VerificationEngine,
    run_reasoning_pipeline,
)
from om_ai.core.intent_engine import classify, route
from om_ai.core.response import check_quality, format_response

__all__ = [
    "IntentAnalyzer",
    "PlanningEngine",
    "SolutionGenerator",
    "VerificationEngine",
    "ReflectionEngine",
    "run_reasoning_pipeline",
    "classify",
    "route",
    "check_quality",
    "format_response",
]
