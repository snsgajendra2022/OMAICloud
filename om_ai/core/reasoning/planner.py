"""Planning engine — ordered steps from intent."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .analyzer import IntentResult


@dataclass
class PlanResult:
    plan: list[str] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"plan": self.plan, "agents": self.agents, "meta": self.meta}


class PlanningEngine:
    def plan(self, intent: IntentResult) -> PlanResult:
        base = [
            "Clarify success criteria",
            "Retrieve relevant knowledge",
            "Draft approach",
            "Execute safest next step",
            "Validate result",
        ]
        agents = ["master"]
        if intent.intent in {"coding", "debug", "architecture"}:
            base = [
                "Map repository / interfaces",
                "Retrieve docs + prior decisions",
                "Write failing test or reproduction",
                "Implement minimal change",
                "Run tests and review security",
            ]
            agents = ["master", "coding", "testing", "security"]
        elif intent.intent == "research":
            agents = ["master", "research", "science"]
        elif intent.intent == "business":
            agents = ["master", "business", "data"]
        return PlanResult(plan=base, agents=agents, meta={"planner": "om-plan-v1"})
