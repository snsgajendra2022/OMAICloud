from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class DialogueContext:
    topic: str = ""
    mood: str = "neutral"
    open_thread: str = ""
    turns: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"topic": self.topic, "mood": self.mood, "open_thread": self.open_thread, "turns": self.turns}

class ContextTracker:
    def __init__(self) -> None:
        self.ctx = DialogueContext()

    def update(self, *, intent: str = "", mood: str = "") -> DialogueContext:
        self.ctx.turns += 1
        if intent:
            self.ctx.topic = intent
            self.ctx.open_thread = intent
        if mood:
            self.ctx.mood = mood
        return self.ctx
