"""Memory microservice — layered memory."""
from __future__ import annotations

from typing import Any

from services._common import ServiceHealth, ok


class MemoryService:
    def __init__(self, db: str = "artifacts/om_ai.sqlite3") -> None:
        self.db = db

    def health(self) -> dict[str, Any]:
        return ServiceHealth("memory-service", detail={"backend": "sqlite+layers"}).to_dict()

    def remember_project(self, project: str, stack: list[str], decisions: str = "") -> dict[str, Any]:
        from om_ai.memory.layers import LayeredMemory

        mid = LayeredMemory(self.db).remember_project(project, stack, decisions)
        return ok({"id": mid})

    def recall(self, query: str, *, layer: str | None = None) -> dict[str, Any]:
        from om_ai.memory.layers import LayeredMemory

        return ok(LayeredMemory(self.db).recall(query, layer=layer))
