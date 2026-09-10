"""
OM Cognitive Intelligence Layer.

This package exposes the core cognitive systems used by OM:

- Cognitive Engine
- OM Cognitive Brain pipeline
- Reasoning Engine
- Planning Engine
- Decision Engine
- Self Evaluation
- Cognitive Response Engine
- Agent Collaboration
- Context Management
- Intelligence State
- Research Intelligence
- Response Intelligence utilities

Important:
This module only exposes package components.

Runtime processing, research execution, model generation,
memory retrieval, tool execution, and response planning belong
inside the cognitive/brain pipeline and must not execute here.
"""

from __future__ import annotations


# ============================================================
# Cognitive Core
# ============================================================

from .cognitive_engine import CognitiveEngine
from .brain_pipeline import OMCognitiveBrain
from .reasoning_engine import ReasoningEngine
from .planner import PlanningEngine
from .decision_engine import DecisionEngine
from .self_evaluator import SelfEvaluator
from .response_engine import (
    ResponseEngine as CognitiveResponseEngine,
)
from .agent_collaboration import AgentCollaboration
from .context_manager import ContextManager
from .intelligence_state import IntelligenceState


# ============================================================
# Research Intelligence
# ============================================================

from om_ai.core.research import (
    ResearchEngine,
    ResearchState,
    ResearchSource,
    SearchResult,
    WebConnector,
    SearchProvider,
)


# ============================================================
# Final Response Intelligence
# ============================================================

from om_ai.core.response.response_engine import (
    ResponseEngine,
)

from om_ai.core.response.quality_checker import (
    QualityChecker,
)

from om_ai.core.response.self_critic import (
    SelfCritic,
)

from om_ai.core.response.context_filter import (
    ContextFilter,
)

from om_ai.core.response.response_memory import (
    ResponseMemory,
)


# ============================================================
# Compatibility Alias
# ============================================================

# Older code may import:
#
# from om_ai.core.cognitive import Planner
#
# Keep this alias for backward compatibility.
Planner = PlanningEngine


# ============================================================
# Public API
# ============================================================

__all__ = [

    # Cognitive brain
    "CognitiveEngine",
    "OMCognitiveBrain",

    # Reasoning / planning
    "ReasoningEngine",
    "Planner",
    "PlanningEngine",
    "DecisionEngine",

    # Evaluation
    "SelfEvaluator",

    # Response engines
    "ResponseEngine",
    "CognitiveResponseEngine",

    # Agent system
    "AgentCollaboration",

    # Context / state
    "ContextManager",
    "IntelligenceState",

    # Research intelligence
    "ResearchEngine",
    "ResearchState",
    "ResearchSource",
    "SearchResult",
    "WebConnector",
    "SearchProvider",

    # Response intelligence
    "QualityChecker",
    "SelfCritic",
    "ContextFilter",
    "ResponseMemory",
]