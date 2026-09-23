"""STEP 26 — OM Chat Intelligence Core (ChatGPT-like Conversation Brain).

Flow:
  User → Understand → Remember → Plan → Solve → Generate → Improve → Answer

Solution intelligence:
  problem → hypotheses → plan → reason → explain → verify → correct → confidence → memory
"""
from __future__ import annotations

from .answer_planner import AnswerPlanner
from .chat_orchestrator import ChatOrchestrator, run_chat_intelligence
from .chat_quality_engine import ChatQualityEngine
from .coding_engine import CodingEngine
from .confidence_engine import ConfidenceEngine
from .context_manager import ContextManager
from .conversation_engine import ConversationEngine
from .conversation_memory import ConversationMemory
from .conversation_router import ConversationRouter
from .correction_engine import CorrectionEngine
from .emotional_engine import EmotionalEngine
from .explanation_engine import ExplanationEngine
from .hypothesis_engine import HypothesisEngine
from .intent_understanding import IntentResult, IntentUnderstanding
from .personality_engine import PersonalityEngine
from .problem_analyzer import ProblemAnalyzer
from .reasoning_engine import ReasoningEngine
from .research_engine import ResearchEngine
from .response_optimizer import ResponseOptimizer
from .safety_filter import SafetyFilter
from .action_engine import ActionEngine
from .solution_engine import SolutionEngine
from .solution_memory import SolutionMemory
from .solution_planner import SolutionPlanner
from .user_preference import UserPreference
from .verification_engine import VerificationEngine

__all__ = [
    "ActionEngine",
    "AnswerPlanner",
    "ChatOrchestrator",
    "ChatQualityEngine",
    "CodingEngine",
    "ConfidenceEngine",
    "ContextManager",
    "ConversationEngine",
    "ConversationMemory",
    "ConversationRouter",
    "CorrectionEngine",
    "EmotionalEngine",
    "ExplanationEngine",
    "HypothesisEngine",
    "IntentResult",
    "IntentUnderstanding",
    "PersonalityEngine",
    "ProblemAnalyzer",
    "ReasoningEngine",
    "ResearchEngine",
    "ResponseOptimizer",
    "SafetyFilter",
    "SolutionEngine",
    "SolutionMemory",
    "SolutionPlanner",
    "UserPreference",
    "VerificationEngine",
    "run_chat_intelligence",
]
