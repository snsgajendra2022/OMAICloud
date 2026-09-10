"""STEP 90 — Agent Collaboration Upgrade.

Planner / Research / Coding / Testing / Security / Review / Deployment / Coordinator.
"""
from __future__ import annotations

from typing import Any

from .step85_agent_civilization import AgentCivilization


class AgentCollaborationUpgrade:
    SPECIALISTS = [
        "planner",
        "research",
        "coding",
        "testing",
        "security",
        "review",
        "deployment",
        "coordinator",
    ]

    def __init__(self) -> None:
        self.civilization = AgentCivilization()

    def collaborate(self, goal: str) -> dict[str, Any]:
        civ = self.civilization.run(goal)
        # Map civilization agents into STEP-90 specialist lanes
        lanes = {name: [] for name in self.SPECIALISTS}
        for task in civ.get("tasks") or []:
            agent = task.get("agent")
            mapping = {
                "planner": "planner",
                "research": "research",
                "frontend": "coding",
                "backend": "coding",
                "database": "coding",
                "qa": "testing",
                "security": "security",
                "review": "review",
                "deploy": "deployment",
                "coordinator": "coordinator",
            }
            lane = mapping.get(agent, "coordinator")
            lanes[lane].append(task.get("output") or "")

        board = []
        for lane, outputs in lanes.items():
            if outputs:
                board.append({"agent": lane, "outputs": outputs})

        final = [
            f"Collaboration board for: {goal}",
            "",
        ]
        for row in board:
            final.append(f"## {row['agent'].title()} Agent")
            for o in row["outputs"]:
                final.append(f"- {o}")
            final.append("")
        final.append("Coordinator Agent merges the above into one delivery sequence.")

        return {
            "step": 90,
            "goal": goal,
            "board": board,
            "agents_used": [r["agent"] for r in board],
            "summary": "\n".join(final),
            "civilization": {
                "agents": civ.get("agents"),
                "status": civ.get("status"),
            },
        }
