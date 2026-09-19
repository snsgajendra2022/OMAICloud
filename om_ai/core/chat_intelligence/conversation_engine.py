"""Conversation engine — identity / name as data. No canned greeting bank."""
from __future__ import annotations

import re
from typing import Any

from .intent_understanding import IntentResult, IntentUnderstanding


class ConversationEngine:
    """Handle user-name as structured memory. Social talk goes to the brain."""

    def __init__(self) -> None:
        self.intent = IntentUnderstanding()

    def detect(self, message: str, *, history: list[dict] | None = None) -> IntentResult:
        return self.intent.understand(message, history=history)

    def can_handle(self, intent: IntentResult | dict[str, Any]) -> bool:
        if isinstance(intent, IntentResult):
            name = intent.intent
            needs_model = intent.needs_model
        else:
            name = str(intent.get("intent") or "")
            needs_model = bool(intent.get("needs_model", True))
        return (not needs_model) and name in {"user_name", "user_name_set"}

    def respond(self, intent_name: str, *, user_name: str = "") -> str:
        del intent_name, user_name
        return ""

    def _extract_name(self, message: str) -> str:
        m = IntentUnderstanding.USER_NAME_SET.search(message or "")
        if not m:
            return ""
        name = re.sub(r"[^A-Za-z\s]", "", m.group(1) or "").strip()
        parts = [p.capitalize() for p in name.split() if p][:3]
        return " ".join(parts)[:40]

    def process(
        self,
        message: str,
        *,
        history: list[dict] | None = None,
        user_name: str = "",
        voice_mode: bool = False,
        skip_canned: bool = False,
    ) -> dict[str, Any]:
        del voice_mode, skip_canned
        intent = self.detect(message, history=history)
        if not self.can_handle(intent):
            return {
                "handled": False,
                "intent": intent.to_dict(),
                "response": "",
                "strategy": intent.strategy,
            }

        if intent.intent == "user_name_set":
            name = self._extract_name(message) or user_name
            if name:
                return {
                    "handled": True,
                    "intent": intent.to_dict(),
                    "response": f"Got it, {name}. I'll remember that.",
                    "strategy": intent.strategy,
                    "remember_name": name,
                }
            return {
                "handled": False,
                "intent": intent.to_dict(),
                "response": "",
                "strategy": intent.strategy,
            }

        name = (user_name or "").strip()
        if name:
            reply = f"Your name is {name}."
        else:
            reply = "I don't have your name yet. What should I call you?"
        return {
            "handled": True,
            "intent": intent.to_dict(),
            "response": reply,
            "strategy": intent.strategy,
        }
