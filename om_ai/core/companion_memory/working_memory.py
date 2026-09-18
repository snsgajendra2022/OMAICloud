"""Short-term working memory (in-process, per session)."""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from .memory_event import MemoryEvent


class WorkingMemory:
    """Recent turns and scratch facts for the active session."""

    def __init__(self, *, max_items: int = 24) -> None:
        self.max_items = max_items
        self._by_session: dict[str, deque[MemoryEvent]] = defaultdict(
            lambda: deque(maxlen=self.max_items)
        )

    def push(self, session_id: str, event: MemoryEvent) -> None:
        self._by_session[session_id].append(event)

    def items(self, session_id: str, *, limit: int = 12) -> list[MemoryEvent]:
        q = self._by_session.get(session_id)
        if not q:
            return []
        return list(q)[-limit:]

    def as_dicts(self, session_id: str, *, limit: int = 12) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.items(session_id, limit=limit)]

    def clear(self, session_id: str) -> None:
        self._by_session.pop(session_id, None)

    def clear_all(self) -> None:
        self._by_session.clear()
