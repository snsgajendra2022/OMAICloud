from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ConversationContext:
    topic: str = ""
    mood: str = "neutral"
    last_intent: str = ""
    open_loops: list[str] = field(default_factory=list)
    relationship_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "mood": self.mood,
            "last_intent": self.last_intent,
            "open_loops": list(self.open_loops),
            "relationship_note": self.relationship_note,
        }

class ContextTracker:
    def __init__(self) -> None:
        self.ctx = ConversationContext()

    def update(self, *, topic: str = "", mood: str = "", intent: str = "") -> ConversationContext:
        if topic:
            self.ctx.topic = topic
        if mood:
            self.ctx.mood = mood
        if intent:
            self.ctx.last_intent = intent
        return self.ctx
