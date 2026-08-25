"""Lightweight knowledge graph for OM foundation (JSON-backed)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class KnowledgeGraph:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._nodes: set[str] = set()
        self._edges: list[dict[str, str]] = []
        if self.path.is_file():
            data = json.loads(self.path.read_text(encoding="utf-8") or "{}")
            self._nodes = set(data.get("nodes") or [])
            self._edges = list(data.get("edges") or [])

    def add_triple(self, subject: str, relation: str, obj: str) -> None:
        self._nodes.add(subject)
        self._nodes.add(obj)
        edge = {"s": subject, "r": relation, "o": obj}
        if edge not in self._edges:
            self._edges.append(edge)

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self._edges)

    def neighbors(self, node: str) -> list[dict[str, str]]:
        return [e for e in self._edges if e["s"] == node or e["o"] == node]

    def save(self) -> None:
        payload = {
            "nodes": sorted(self._nodes),
            "edges": self._edges,
        }
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def to_dict(self) -> dict[str, Any]:
        return {"nodes": sorted(self._nodes), "edges": self._edges, "path": str(self.path)}
