from __future__ import annotations
from typing import Any

from .context_tracker import ContextTracker
from .conversation_flow import ConversationFlow
from .relationship_engine import RelationshipEngine
from .turn_manager import TurnManager

_RT = None

class HumanConversationRuntime:
    def __init__(self) -> None:
        self.flow = ConversationFlow()
        self.turns = TurnManager()
        self.context = ContextTracker()
        self.relationship = RelationshipEngine()

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "name": "Human Conversation Engine",
            "relationship": self.relationship.to_dict(),
            "context": self.context.ctx.to_dict(),
        }

    def respond(self, text: str, *, locale: str = "en") -> dict[str, Any]:
        intent = self.flow.intent(text)
        self.context.update(intent=intent, mood=intent)
        self.turns.add("user", text, intent=intent)
        reply = self.flow.human_reply(
            text,
            locale=locale,
            address=self.relationship.address_line(locale),
        )
        if reply:
            self.turns.add("assistant", reply, intent=intent)
        return {
            "intent": intent,
            "reply": reply,
            "handled": bool(reply),
            "context": self.context.ctx.to_dict(),
            "relationship": self.relationship.to_dict(),
        }


def get_human_conversation() -> HumanConversationRuntime:
    global _RT
    if _RT is None:
        _RT = HumanConversationRuntime()
    return _RT
