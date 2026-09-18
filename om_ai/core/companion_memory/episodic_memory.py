"""Episodic memory — conversation episodes and experiences."""
from __future__ import annotations

from typing import Any

from .memory_event import MemoryEvent


class EpisodicMemory:
    """Time-ordered episodes keyed by user/session."""

    KIND = "episodic"

    def __init__(self, store: dict[str, list[dict[str, Any]]]) -> None:
        self._store = store

    def _bucket(self, session_key: str) -> list[dict[str, Any]]:
        return self._store.setdefault(session_key, [])

    def append(
        self,
        session_key: str,
        content: str,
        *,
        tags: list[str] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> MemoryEvent:
        ev = MemoryEvent(
            kind=self.KIND,
            content=content,
            scope="session",
            key=session_key,
            tags=list(tags or []),
            meta=dict(meta or {}),
        )
        bucket = self._bucket(session_key)
        bucket.append(ev.to_dict())
        if len(bucket) > 200:
            del bucket[:-200]
        return ev

    def list(self, session_key: str, *, limit: int = 50) -> list[dict[str, Any]]:
        return list(self._bucket(session_key)[-limit:])

    def clear(self, session_key: str) -> int:
        n = len(self._bucket(session_key))
        self._store.pop(session_key, None)
        return n
