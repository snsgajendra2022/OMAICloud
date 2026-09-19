"""Continuous turn tracking with overlap / barge-in support."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Turn:
    turn_id: str
    role: str
    text: str
    ts: float = field(default_factory=time.time)
    interrupted: bool = False
    topic: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "role": self.role,
            "text": self.text,
            "ts": self.ts,
            "interrupted": self.interrupted,
            "topic": self.topic,
        }


class TurnManager:
    def __init__(self, max_turns: int = 80) -> None:
        self.turns: list[Turn] = []
        self.max_turns = max_turns
        self.active_assistant_id: str | None = None

    def begin_user(self, text: str, *, topic: str = "") -> Turn:
        t = Turn(str(uuid.uuid4()), "user", text, topic=topic)
        self.turns.append(t)
        self._trim()
        return t

    def begin_assistant(self, text: str, *, topic: str = "") -> Turn:
        t = Turn(str(uuid.uuid4()), "assistant", text, topic=topic)
        self.active_assistant_id = t.turn_id
        self.turns.append(t)
        self._trim()
        return t

    def mark_interrupted(self) -> Turn | None:
        if not self.active_assistant_id:
            return None
        for t in reversed(self.turns):
            if t.turn_id == self.active_assistant_id:
                t.interrupted = True
                self.active_assistant_id = None
                return t
        return None

    def history(self, limit: int = 20) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self.turns[-limit:]]

    def _trim(self) -> None:
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns :]
