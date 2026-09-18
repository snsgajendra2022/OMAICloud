"""Track partial/final transcripts for a session."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


@dataclass
class TranscriptTurn:
    text: str
    final: bool = False
    confidence: float = 0.0
    turn_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "text": self.text,
            "final": self.final,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }


class TranscriptManager:
    def __init__(self) -> None:
        self.partial: str = ""
        self.finals: list[TranscriptTurn] = []

    def set_partial(self, text: str, *, confidence: float = 0.0) -> TranscriptTurn:
        self.partial = (text or "").strip()
        return TranscriptTurn(text=self.partial, final=False, confidence=confidence)

    def commit_final(self, text: str, *, confidence: float = 0.0) -> TranscriptTurn:
        turn = TranscriptTurn(text=(text or "").strip(), final=True, confidence=confidence)
        if turn.text:
            self.finals.append(turn)
        self.partial = ""
        return turn

    def history(self, limit: int = 20) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self.finals[-limit:]]

    def clear(self) -> None:
        self.partial = ""
        self.finals.clear()
