"""Layered memory API over SQLiteMemoryStore (additive, non-breaking)."""
from __future__ import annotations

from typing import Any

from om_ai.memory.sqlite_memory import SQLiteMemoryStore

LAYERS = (
    "short",
    "conversation",
    "user",
    "project",
    "experience",
    "skill",
)

# Map cognitive layers → store kinds
_KIND_FOR_LAYER = {
    "short": "conversation",
    "conversation": "conversation",
    "user": "preference",
    "project": "semantic",
    "experience": "episodic",
    "skill": "task",
}


class LayeredMemory:
    """Project/user/skill memory helpers (e.g. ECTS + FastAPI/Zoho/React)."""

    def __init__(
        self,
        db_path: str = "artifacts/om_ai.sqlite3",
        *,
        tenant_id: str = "default",
        user_id: str = "default",
    ) -> None:
        self.store = SQLiteMemoryStore(db_path)
        self.tenant_id = tenant_id
        self.user_id = user_id

    def remember(
        self,
        layer: str,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        layer = layer if layer in LAYERS else "experience"
        kind = _KIND_FOR_LAYER[layer]
        meta = {"layer": layer, **(metadata or {})}
        return int(
            self.store.add(
                self.tenant_id,
                self.user_id,
                content,
                kind=kind,
                metadata=meta,
                provenance={"source": "layered-memory"},
            )
        )

    def recall(
        self,
        query: str,
        *,
        layer: str | None = None,
        k: int = 5,
    ) -> list[dict[str, Any]]:
        kind = _KIND_FOR_LAYER.get(layer) if layer else None
        hits = self.store.search(
            query,
            self.tenant_id,
            self.user_id,
            kind=kind,
            limit=k,
        ) or []
        out: list[dict[str, Any]] = []
        for h in hits:
            meta = getattr(h, "metadata", {}) or {}
            if isinstance(meta, str):
                import json

                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            if layer and meta.get("layer") not in {layer, None}:
                # allow kind-mapped hits even if older rows lack layer tag
                if meta.get("layer") and meta.get("layer") != layer:
                    continue
            out.append(
                {
                    "id": getattr(h, "id", ""),
                    "content": getattr(h, "content", ""),
                    "kind": getattr(h, "kind", ""),
                    "metadata": meta,
                }
            )
        return out

    def remember_project(self, project: str, stack: list[str], decisions: str = "") -> int:
        body = (
            f"Project: {project}\n"
            f"Stack: {', '.join(stack)}\n"
            f"Previous decisions: {decisions or '(none yet)'}"
        )
        return self.remember(
            "project",
            body,
            metadata={"project": project, "stack": stack},
        )
