from __future__ import annotations
from typing import Any

from .context_tracker import ContextTracker
from .conversation_flow import ConversationFlow
from .interruption_handler import InterruptionHandler
from .relationship_manager import RelationshipManager
from .social_intelligence import SocialIntelligence

_RT = None

class HumanDialogueRuntime:
    def __init__(self) -> None:
        self.flow = ConversationFlow()
        self.context = ContextTracker()
        self.relationship = RelationshipManager()
        self.interruptions = InterruptionHandler()
        self.social = SocialIntelligence()

    def status(self) -> dict[str, Any]:
        return {"ready": True, "step": 101, "name": "Human Dialogue Engine"}

    def respond(self, text: str, *, locale: str = "en", speaking: bool = False) -> dict[str, Any]:
        # Prefer dedicated natural replies; fall back to human_conversation package
        intent = self.flow.natural.detect(text)
        self.context.update(intent=intent, mood=intent)
        address = self.relationship.address(locale)
        reply = self.flow.reply(text, address=address, locale=locale)
        if not reply:
            try:
                from om_ai.core.human_conversation import get_human_conversation
                hc = get_human_conversation().respond(text, locale=locale)
                if hc.get("reply"):
                    reply = str(hc["reply"])
                    intent = str(hc.get("intent") or intent)
            except Exception:
                pass
        if speaking and self.interruptions.should_yield(text, speaking=True):
            reply = self.interruptions.ack(address)
        return {
            "intent": intent,
            "reply": reply,
            "handled": bool(reply),
            "social": self.social.bias(intent),
            "context": self.context.ctx.to_dict(),
            "relationship": self.relationship.to_dict(),
        }

def get_human_dialogue() -> HumanDialogueRuntime:
    global _RT
    if _RT is None:
        _RT = HumanDialogueRuntime()
    return _RT
