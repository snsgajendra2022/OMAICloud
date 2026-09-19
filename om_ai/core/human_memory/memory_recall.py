"""STEP 55/103 human memory runtime."""
from __future__ import annotations
from typing import Any

from .emotional_memory import EmotionalMemory
from .episodic_memory import EpisodicMemory
from .memory_consolidation import MemoryConsolidation
from .preference_memory import PreferenceMemory
from .project_memory import ProjectMemory
from .relationship_memory import RelationshipMemory
from .semantic_memory import SemanticMemory

_RT = None


class HumanMemoryRuntime:
    def __init__(self) -> None:
        self.episodic = EpisodicMemory()
        self.relationship = RelationshipMemory()
        self.preferences = PreferenceMemory()
        self.projects = ProjectMemory()
        self.emotional = EmotionalMemory()
        self.consolidator = MemoryConsolidation()
        self.semantic = SemanticMemory()

    def status(self) -> dict[str, Any]:
        return {"ready": True, "step": 55, "name": "Human Memory Upgrade"}

    def observe_turn(self, user: str, assistant: str = "", *, affect: dict | None = None) -> dict[str, Any]:
        self.episodic.add(user, role="user")
        if assistant:
            self.episodic.add(assistant, role="assistant")
        prefs = self.preferences.observe(user)
        sem = self.semantic.observe(user)
        if affect and affect.get("label"):
            self.emotional.add(str(affect["label"]), text=user)
        summary = self.consolidator.summarize(self.episodic.recent(8))
        return {
            "preferences": prefs,
            "semantic": sem,
            "relationship": self.relationship.to_dict(),
            "projects": self.projects.to_dict(),
            "summary": summary,
        }

    def recall_blob(self) -> str:
        prefs = self.preferences.to_dict()
        rel = self.relationship.to_dict()
        proj = self.projects.to_dict()
        sem = self.semantic.to_dict()
        parts = [
            f"Address as: {rel.get('address_as') or 'Sir'}",
            f"Detail preference: {prefs.get('detail') or sem.get('detail_preference')}",
            f"Active project: {proj.get('active') or sem.get('active_project') or 'OM AI'}",
            self.consolidator.summarize(self.episodic.recent(6)),
        ]
        return "\n".join(p for p in parts if p)


def get_human_memory() -> HumanMemoryRuntime:
    global _RT
    if _RT is None:
        _RT = HumanMemoryRuntime()
    return _RT
