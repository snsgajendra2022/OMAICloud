"""Semantic memory — stable facts and concepts."""
from __future__ import annotations

from typing import Any

from .memory_event import MemoryEvent


class SemanticMemory:
    """Facts indexed by topic key within a user scope."""

    KIND = "semantic"

    def __init__(self, store: dict[str, list[dict[str, Any]]]) -> None:
        self._store = store

    def _bucket(self, user_key: str) -> list[dict[str, Any]]:
        return self._store.setdefault(user_key, [])

    def upsert(
        self,
        user_key: str,
        topic: str,
        fact: str,
        *,
        meta: dict[str, Any] | None = None,
    ) -> MemoryEvent:
        ev = MemoryEvent(
            kind=self.KIND,
            content=fact,
            scope="user",
            key=topic,
            tags=[topic] if topic else [],
            meta=dict(meta or {}),
        )
        bucket = self._bucket(user_key)
        replaced = False
        for i, row in enumerate(bucket):
            if row.get("key") == topic and row.get("kind") == self.KIND:
                bucket[i] = ev.to_dict()
                replaced = True
                break
        if not replaced:
            bucket.append(ev.to_dict())
        if len(bucket) > 500:
            del bucket[:-500]
        return ev

    def list(self, user_key: str, *, limit: int = 100) -> list[dict[str, Any]]:
        return list(self._bucket(user_key)[-limit:])

    def clear(self, user_key: str) -> int:
        n = len(self._bucket(user_key))
        self._store.pop(user_key, None)
        return n
