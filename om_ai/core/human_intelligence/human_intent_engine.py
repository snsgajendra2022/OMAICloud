"""Human intent engine — request / share / act / joke / think / research."""
from __future__ import annotations

import re
from typing import Any


class HumanIntentEngine:
    def infer(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        meaning: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        low = (message or "").lower().strip()
        meaning = meaning or {}

        if meaning.get("needs_listening") or meaning.get("user_is_sharing"):
            return {
                "intent": "sharing",
                "goal": "be_heard",
                "needs": "conversation",
                "action": "listen",
                "confidence": 0.9,
            }

        if re.search(r"(?i)\b(search|google|khoj|research|look\s+up|find\s+(me\s+)?(the\s+)?)\b", low):
            return {
                "intent": "research",
                "goal": "information",
                "needs": "search_summarize",
                "action": "search_only",
                "confidence": 0.88,
            }

        if re.search(r"(?i)\b(open|kholo|khol|launch|start|delete|send|run|execute)\b", low):
            return {
                "intent": "action",
                "goal": "do_something",
                "needs": "permission",
                "action": "ask_then_execute",
                "confidence": 0.86,
            }

        if re.search(r"(?i)\b(joke|majaak|funny|haha|lol)\b", low):
            return {
                "intent": "joke",
                "goal": "play",
                "needs": "humor",
                "action": "light_reply",
                "confidence": 0.8,
            }

        if re.search(r"(?i)^\s*(hey|hi|hello|namaste|yo)\b", low):
            return {
                "intent": "greeting",
                "goal": "presence",
                "needs": "acknowledge",
                "action": "greet",
                "confidence": 0.92,
            }

        if "?" in (message or "") or re.search(
            r"(?i)\b(what|how|why|when|where|kaise|kya|kyun|explain)\b", low
        ):
            return {
                "intent": "question",
                "goal": "answer",
                "needs": "clear_answer",
                "action": "answer",
                "confidence": 0.84,
            }

        if re.search(r"(?i)\b(fix|error|bug|debug|not working|crash)\b", low):
            return {
                "intent": "problem",
                "goal": "solve",
                "needs": "reasoning",
                "action": "analyze_then_help",
                "confidence": 0.85,
            }

        if re.search(r"(?i)\b(thinking|soch|maybe|perhaps|hmm+)\b", low):
            return {
                "intent": "thinking",
                "goal": "reflect",
                "needs": "space",
                "action": "think_with",
                "confidence": 0.7,
            }

        return {
            "intent": "conversation",
            "goal": "continue",
            "needs": "assist",
            "action": "reply",
            "confidence": 0.6,
        }


# Backward-compatible alias used elsewhere
IntentUnderstanding = HumanIntentEngine
