"""Conversation engine — social / greeting / identity fast path."""
from __future__ import annotations

import random
from typing import Any

from .intent_understanding import IntentResult, IntentUnderstanding


class ConversationEngine:
    """Handle greetings, identity, thanks, goodbye without the small model."""

    RESPONSES: dict[str, list[str]] = {
        "identity": [
            "I'm OM AI, your private AI assistant. How can I help you today?",
            "My name is OM. I'm your AI assistant — ask me anything.",
        ],
        "morning": [
            "Good morning! How can I help you today?",
            "Good morning! Hope your day is going well — what would you like to work on?",
        ],
        "afternoon": [
            "Good afternoon! How can I help you?",
            "Good afternoon — what can I help you with?",
        ],
        "evening": [
            "Good evening! How can I help you?",
            "Good evening — what would you like to tackle?",
        ],
        "greeting": [
            "Hello! I'm OM. How can I help you today?",
            "Hi! Nice to meet you. What can I do for you?",
            "Hey — I'm OM. What are you working on?",
        ],
        "thanks": [
            "You're welcome! Anything else I can help with?",
            "Happy to help. What next?",
        ],
        "goodbye": [
            "Goodbye! Come back anytime.",
            "See you later — I'll be here when you need me.",
        ],
    }

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
        return (not needs_model) and name in self.RESPONSES

    def respond(self, intent_name: str) -> str:
        options = self.RESPONSES.get(intent_name) or self.RESPONSES["greeting"]
        return random.choice(options)

    def process(
        self,
        message: str,
        *,
        history: list[dict] | None = None,
    ) -> dict[str, Any]:
        intent = self.detect(message, history=history)
        if self.can_handle(intent):
            return {
                "handled": True,
                "intent": intent.to_dict(),
                "response": self.respond(intent.intent),
                "strategy": intent.strategy,
            }
        return {
            "handled": False,
            "intent": intent.to_dict(),
            "response": "",
            "strategy": intent.strategy,
        }
