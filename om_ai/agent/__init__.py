"""OM Agent Brain v1 — ChatGPT-style assistant layer on top of OM-1.0.

This is the system layer (intent → memory/RAG/tools → plan → verify → reply).
It does **not** make a 20M model equal GPT-4; it makes OM behave like a
professional assistant using architecture the tiny model cannot provide alone.
"""
from __future__ import annotations

from om_ai.agent.brain import AgentBrain, AgentDecision
from om_ai.agent.intent import ChatIntent, classify_intent

__all__ = [
    "AgentBrain",
    "AgentDecision",
    "ChatIntent",
    "classify_intent",
]
