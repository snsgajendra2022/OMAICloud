"""Structured semantic frame for companion brain turns."""
from __future__ import annotations

import re
from typing import Any

from om_ai.core.chat_intelligence.intent_understanding import IntentResult

from .goal_engine import GoalEngine

_ACTION_RE = re.compile(
    r"\b("
    r"open|launch|start|close|quit|kholo|khol|"
    r"delete|remove|erase|"
    r"list\s+files|show\s+files|"
    r"run\s+(?:the\s+)?(?:app|script)|execute|install|send\s+email|publish|navigate|"
    r"youtube|google|browser|volume|awaz|mute|unmute|"
    r"weather|mausam|forecast|screenshot|calculator|"
    r"shutdown|restart|sleep"
    r")\b",
    re.I,
)


class SemanticUnderstanding:
    def __init__(self) -> None:
        self.goals = GoalEngine()

    def compose(
        self,
        message: str,
        intent: IntentResult,
        *,
        history: list[dict[str, Any]] | None = None,
        followup: bool = False,
    ) -> dict[str, Any]:
        hist = history or []
        goal = self.goals.infer(intent.intent, followup=followup or bool(hist))
        mode = self._conversation_mode(intent, followup=followup, history=hist)
        requires_memory = mode in {"assist", "continue", "project"} and bool(hist)
        requires_model = bool(intent.needs_model)
        text = (message or "").strip()
        action_like = bool(_ACTION_RE.search(text))
        # Pronoun follow-ups after prior project/action context
        if followup and re.search(r"\b(it|that|this|them)\b", text, re.I) and hist:
            prior = " ".join(str(h.get("content") or "") for h in hist[-4:]).lower()
            if any(k in prior for k in ("project", "folder", "file", "vscode", "code", "open")):
                action_like = True
        requires_action = action_like
        requires_clarification = bool(intent.needs_details) and not action_like
        domain = intent.domain or "general"
        if action_like:
            mode = "task"
            domain = "action"
        return {
            "intent": "action_request" if action_like else intent.intent,
            "goal": "execute_action" if action_like else goal,
            "domain": domain,
            "conversation_mode": mode,
            "requires_memory": requires_memory or action_like,
            "requires_model": requires_model and not action_like,
            "requires_action": requires_action,
            "requires_clarification": requires_clarification,
            "confidence": float(intent.confidence),
            "strategy": intent.strategy,
            "signals": list(intent.signals) + (["action_verb"] if action_like else []),
            "message_len": len(text.split()),
        }

    def _conversation_mode(
        self,
        intent: IntentResult,
        *,
        followup: bool,
        history: list[dict[str, Any]],
    ) -> str:
        if intent.intent in {
            "greeting",
            "morning",
            "afternoon",
            "evening",
            "thanks",
            "goodbye",
            "identity",
            "user_name",
            "user_name_set",
        }:
            return "social"
        if followup or (history and intent.intent == "followup"):
            return "continue"
        if intent.intent in {"debugging", "coding", "howto"}:
            return "task"
        if intent.needs_details:
            return "clarify"
        return "assist"
