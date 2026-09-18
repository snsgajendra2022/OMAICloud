"""Companion memory event records."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MemoryEvent:
    """Single storable memory unit with metadata."""

    kind: str
    content: str
    scope: str = "user"
    key: str = ""
    id: str = field(default_factory=lambda: uuid4().hex[:16])
    created_at: str = field(default_factory=_utc_now)
    updated_at: str = field(default_factory=_utc_now)
    tags: list[str] = field(default_factory=list)
    sensitivity: str = "normal"
    source: str = "companion"
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "content": self.content,
            "scope": self.scope,
            "key": self.key,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": list(self.tags),
            "sensitivity": self.sensitivity,
            "source": self.source,
            "meta": dict(self.meta),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryEvent:
        return cls(
            id=str(data.get("id") or uuid4().hex[:16]),
            kind=str(data.get("kind") or "note"),
            content=str(data.get("content") or ""),
            scope=str(data.get("scope") or "user"),
            key=str(data.get("key") or ""),
            created_at=str(data.get("created_at") or _utc_now()),
            updated_at=str(data.get("updated_at") or _utc_now()),
            tags=[str(t) for t in (data.get("tags") or [])],
            sensitivity=str(data.get("sensitivity") or "normal"),
            source=str(data.get("source") or "companion"),
            meta=dict(data.get("meta") or {}),
        )
