"""STEP 109 — Goal → Plan → Execute → Observe → Improve."""
from __future__ import annotations
from typing import Any

from .evaluator import Evaluator
from .observer import Observer
from .planner import Planner
from .task_graph import TaskGraph
from .worker import Worker

class AgentLoop:
    def __init__(self) -> None:
        self.planner = Planner()
        self.graph = TaskGraph()
        self.worker = Worker()
        self.observer = Observer()
        self.evaluator = Evaluator()

    def run(self, goal: str, *, execute: bool = False) -> dict[str, Any]:
        plan: dict[str, Any]
        try:
            plan = self.planner.plan({"goal": "debug_issue" if "fix" in (goal or "").lower() or "quality" in (goal or "").lower() else "assist"})
        except Exception:
            plan = {"steps": []}
        steps = plan.get("steps") if isinstance(plan, dict) else []
        if not steps:
            # fall back to action engine plan shape
            try:
                from om_ai.core.action_engine import get_action_engine
                plan = get_action_engine().plan(goal, execute=False)
                steps = plan.get("steps") or []
            except Exception:
                steps = [{"id": "1", "label": str(goal)}]
        # normalize step labels for graph
        norm = []
        for i, s in enumerate(steps):
            if isinstance(s, dict):
                norm.append({
                    "id": str(s.get("id") or i + 1),
                    "label": str(s.get("label") or s.get("action") or s.get("id") or f"step-{i+1}"),
                    "deps": s.get("deps") or [],
                })
            else:
                norm.append({"id": str(i + 1), "label": str(s), "deps": []})
        g = self.graph.build(norm)
        results = [self.worker.run(n, execute=execute) for n in g["nodes"]]
        obs = self.observer.note("cycle_complete", {"goal": goal})
        score = self.evaluator.score(results)
        return {"goal": goal, "graph": g, "results": results, "observe": obs, "evaluate": score, "plan": plan}
