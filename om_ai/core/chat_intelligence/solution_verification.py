"""
Compatibility shim — verification lives in verification_engine.py.

Historically this file held a draft SolutionEngine; the real orchestrator is
solution_engine.SolutionEngine. Prefer:

  from om_ai.core.chat_intelligence import SolutionEngine, VerificationEngine
"""
from __future__ import annotations

from .solution_engine import SolutionEngine
from .verification_engine import VerificationEngine

__all__ = ["SolutionEngine", "VerificationEngine"]
