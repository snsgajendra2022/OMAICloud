"""Normalize understanding into canonical intents."""
from __future__ import annotations

from typing import Any


CANONICAL = {
    "question",
    "creation",
    "generation",
    "explanation",
    "debugging",
    "recommendation",
    "calculation",
    "research",
    "planning",
    "comparison",
    "conversation",
    "date_request",
    "prompt_generation",
    "code_creation",
    "unclear",
}


_MAP = {
    "vision_analysis": "vision_analysis",
    "date_request": "date_request",
    "prompt_generation": "prompt_generation",
    "recommendation": "recommendation",
    "code_creation": "creation",
    "explanation": "explanation",
    "debugging": "debugging",
    "research": "research",
    "planning": "planning",
    "comparison": "comparison",
    "calculation": "calculation",
    "conversation": "conversation",
    "question": "question",
    "unclear": "unclear",
}


class IntentEngine:
    def resolve(self, understanding: dict[str, Any]) -> dict[str, Any]:
        raw = str(understanding.get("intent") or "unclear")
        canonical = _MAP.get(raw, raw if raw in CANONICAL else "question")
        return {
            "intent": raw,
            "canonical": canonical,
            "action": understanding.get("action") or "answer",
            "domain": understanding.get("domain") or "general",
            "confidence": float(understanding.get("confidence") or 0.5),
            "needs_clarification": bool(understanding.get("needs_clarification")),
        }
