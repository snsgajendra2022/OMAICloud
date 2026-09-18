"""Conversation memory for OM Chat Intelligence."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Turn:
    role: str
    content: str
    intent: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "intent": self.intent,
            "timestamp": self.timestamp,
        }


class ConversationMemory:
    """Per-session short-term conversation memory."""

    def __init__(self, *, max_turns: int = 40) -> None:
        self.max_turns = max_turns
        self._sessions: dict[str, deque[Turn]] = defaultdict(
            lambda: deque(maxlen=self.max_turns)
        )

    def session_id(self, tenant_id: str = "default", actor: str = "") -> str:
        return f"{tenant_id}:{actor or 'anon'}"

    def add(
        self,
        session: str,
        role: str,
        content: str,
        *,
        intent: str = "",
    ) -> None:
        text = (content or "").strip()
        if not text:
            return
        self._sessions[session].append(
            Turn(role=role, content=text[:4000], intent=intent)
        )

    def history(self, session: str, *, limit: int = 12) -> list[dict[str, Any]]:
        turns = list(self._sessions.get(session) or [])
        return [t.to_dict() for t in turns[-limit:]]

    def recent_user_topics(self, session: str, *, limit: int = 5) -> list[str]:
        out: list[str] = []
        for t in reversed(list(self._sessions.get(session) or [])):
            if t.role == "user":
                out.append(t.content[:160])
                if len(out) >= limit:
                    break
        return list(reversed(out))

    def summary(self, session: str) -> str:
        turns = self.history(session, limit=6)
        if not turns:
            return ""
        parts = [f"{t['role']}: {t['content'][:120]}" for t in turns]
        return " | ".join(parts)[:800]

    def clear(self, session: str) -> None:
        self._sessions.pop(session, None)
