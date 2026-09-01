"""Cognition runtime — intent → reason → retrieve → verify (production path)."""
from __future__ import annotations

from typing import Any

from om_ai.cognition.intent_engine import IntentEngine
from om_ai.cognition.task_planner import TaskPlanner
from om_ai.cognition.technology_engine import TechnologyEngine

__all__ = [
    "CognitionRuntime",
    "IntentEngine",
    "TaskPlanner",
    "TechnologyEngine",
    "think",
]


class CognitionRuntime:
    """End-to-end cognitive pass for user requests."""

    def run(self, question: str, *, tenant_id: str = "default", k: int = 5) -> dict[str, Any]:
        # Import inside the method so package import cannot cycle through solver.
        from om_ai.core.reasoning.pipeline import run_reasoning_pipeline
        from om_ai.knowledge.retrieval import search_knowledge

        hits_raw = search_knowledge(question, tenant_id=tenant_id, k=k)
        hits = [str(h.get("text") or "") for h in hits_raw]
        result = run_reasoning_pipeline(question, knowledge_hits=hits)
        intent = (result.get("intent") or {}).get("intent")
        if intent in {"coding", "architecture", "debug"}:
            result["response_template"] = {
                "title": "Implementation plan ready",
                "sections": [
                    "Understanding",
                    "Architecture",
                    "Files",
                    "Implementation",
                    "Validation",
                    "Next Steps",
                ],
                "note": "Attach larger OM weights for full code emission quality.",
            }
        result["runtime"] = "om-cognition-v1"
        result["knowledge_hits"] = len(hits)
        return result


def think(question: str, **kwargs: Any) -> dict[str, Any]:
    return CognitionRuntime().run(question, **kwargs)
