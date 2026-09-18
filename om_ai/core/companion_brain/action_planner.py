"""Plan companion actions before response generation."""
from __future__ import annotations

from typing import Any


class ActionPlanner:
    def plan(
        self,
        semantic: dict[str, Any],
        policy: dict[str, Any],
        strategy: dict[str, Any],
        *,
        memory_recall: dict[str, Any] | None = None,
        knowledge: dict[str, Any] | None = None,
        reasoning: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        steps: list[str] = []
        if semantic.get("requires_memory"):
            steps.append("recall_context")
        if knowledge and knowledge.get("used"):
            steps.append("attach_knowledge")
        if reasoning and reasoning.get("used"):
            steps.append("attach_reasoning")
        steps.append("generate_reply")
        if policy.get("max_questions", 0) > 0 and semantic.get("requires_clarification"):
            steps.append("optional_clarify")
        return {
            "steps": steps,
            "engine": strategy.get("engine"),
            "style": strategy.get("style"),
            "memory_hits": len((memory_recall or {}).get("hits") or []),
        }
