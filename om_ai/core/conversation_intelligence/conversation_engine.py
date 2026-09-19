"""Conversation intelligence — detect social intent, do not script replies."""
from __future__ import annotations

from typing import Any

from .conversation_router import ConversationRouter
from .social_response import SocialResponseEngine


class ConversationEngine:
    def __init__(self) -> None:
        self.router = ConversationRouter()
        self.response = SocialResponseEngine()

    def process(self, message: str) -> dict[str, Any]:
        intent = self.router.detect(message)
        if not intent:
            return {"handled": False, "intent": None, "response": ""}
        # Intent is a signal only. Spoken text comes from the companion brain.
        return {
            "handled": False,
            "intent": intent,
            "response": "",
            "social_intent": intent,
        }
