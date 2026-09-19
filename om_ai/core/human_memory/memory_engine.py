"""STEP 103 — Unified human memory engine."""
from __future__ import annotations
from typing import Any

from .memory_recall import get_human_memory
from .semantic_memory import SemanticMemory


class MemoryEngine:
    def __init__(self) -> None:
        self.runtime = get_human_memory()
        self.semantic = getattr(self.runtime, "semantic", None) or SemanticMemory()
        if not hasattr(self.runtime, "semantic"):
            self.runtime.semantic = self.semantic

    def status(self) -> dict[str, Any]:
        return {"ready": True, "step": 103, "name": "Human Memory System"}

    def observe(self, user: str, assistant: str = "", *, affect: dict | None = None) -> dict[str, Any]:
        pack = self.runtime.observe_turn(user, assistant, affect=affect)
        pack["semantic"] = self.semantic.observe(user)
        return pack

    def recall(self) -> str:
        blob = self.runtime.recall_blob()
        sem = self.semantic.to_dict()
        return (
            f"{blob}\nSemantic: prefers {sem.get('detail_preference')}; "
            f"project {sem.get('active_project')}"
        )


def get_memory_engine() -> MemoryEngine:
    return MemoryEngine()
