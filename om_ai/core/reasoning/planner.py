"""Planning engine — ordered steps from intent."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .analyzer import PERFORMANCE_CAUSES, IntentResult


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
        meta: dict[str, Any] = {"planner": "om-plan-v2"}
        if intent.intent == "performance":
            causes = list(intent.meta.get("causes") or PERFORMANCE_CAUSES)
            base = [
                "Confirm the symptom and when it started",
                "Check possible causes: " + ", ".join(causes),
                "Gather evidence (waterfall, slow query log, bundle size) before scaling",
                "Fix the cheapest confirmed bottleneck first",
                "Re-measure",
            ]
            agents = ["master", "coding", "testing"]
            meta["causes"] = causes
            meta["avoid"] = intent.meta.get("avoid") or "Do not immediately say increase server"
        elif intent.intent in {"coding", "debug", "architecture"}:
            base = [
                "Map requirement → architecture → technology",
                "Cover frontend, backend, data, auth, and security when building apps",
                "Implement the smallest complete slice",
                "Add tests and validation",
                "Note deployment and secrets handling",
            ]
            agents = ["master", "coding", "testing", "security"]
        elif intent.intent == "research":
            agents = ["master", "research", "science"]
        elif intent.intent == "business":
            agents = ["master", "business", "data"]
        return PlanResult(plan=base, agents=agents, meta=meta)
