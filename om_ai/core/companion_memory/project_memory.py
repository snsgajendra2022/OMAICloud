"""Project-scoped memory."""
from __future__ import annotations

from typing import Any

from .memory_event import MemoryEvent


class ProjectMemory:
    """Notes and milestones per project id."""

    KIND = "project"

    def __init__(self, store: dict[str, list[dict[str, Any]]]) -> None:
        self._store = store

    def _bucket(self, project_key: str) -> list[dict[str, Any]]:
        return self._store.setdefault(project_key, [])

    def add_note(
        self,
        project_key: str,
        note: str,
        *,
        tags: list[str] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> MemoryEvent:
        ev = MemoryEvent(
            kind=self.KIND,
            content=note,
            scope="project",
            key=project_key,
            tags=list(tags or ["project"]),
            meta=dict(meta or {}),
        )
        bucket = self._bucket(project_key)
        bucket.append(ev.to_dict())
        if len(bucket) > 300:
            del bucket[:-300]
        return ev

    def list(self, project_key: str, *, limit: int = 80) -> list[dict[str, Any]]:
        return list(self._bucket(project_key)[-limit:])

    def clear(self, project_key: str) -> int:
        n = len(self._bucket(project_key))
        self._store.pop(project_key, None)
        return n
