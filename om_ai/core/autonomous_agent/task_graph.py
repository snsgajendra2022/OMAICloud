from __future__ import annotations
from typing import Any

class TaskGraph:
    def build(self, steps: list[dict[str, Any]]) -> dict[str, Any]:
        nodes = [{"id": s.get("id"), "label": s.get("label"), "deps": s.get("deps") or []} for s in steps]
        return {"nodes": nodes, "edges": [(d, n["id"]) for n in nodes for d in n["deps"]]}
