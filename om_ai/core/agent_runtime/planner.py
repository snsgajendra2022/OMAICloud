"""Agent planning for STEP 26."""
from __future__ import annotations

from typing import Any

from .agent_goal import AgentGoal
from .task_queue import AgentTask


class AgentPlanner:
    """Turn a user task into goals + prioritized agent tasks."""

    ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
        "coding": (
            "code",
            "bug",
            "python",
            "react",
            "build",
            "implement",
            "api",
            "software",
            "architecture",
        ),
        "research": (
            "research",
            "search",
            "compare",
            "latest",
            "analyze",
            "study",
        ),
        "knowledge": ("knowledge", "explain", "what is", "define", "concept"),
        "security": ("security", "auth", "threat", "vulnerability", "secure"),
        "quality": ("test", "qa", "quality", "review", "validate"),
        "memory": ("remember", "recall", "history", "context"),
    }

    def detect_roles(self, task: str) -> list[str]:
        low = (task or "").lower()
        roles: list[str] = []
        for role, words in self.ROLE_KEYWORDS.items():
            if any(w in low for w in words):
                roles.append(role)
        if not roles:
            roles = ["research", "knowledge"]
        if "quality" not in roles:
            roles.append("quality")
        # de-dupe preserve order
        return list(dict.fromkeys(roles))

    def create_goal(self, task: str, *, priority: float = 0.7) -> AgentGoal:
        roles = self.detect_roles(task)
        return AgentGoal(
            description=(task or "").strip()[:500],
            priority=priority,
            owner=roles[0] if roles else "general",
            success_criteria=[
                "plan created",
                "tasks executed",
                "quality reviewed",
            ],
            metadata={"roles": roles},
        )

    def plan(
        self,
        task: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = dict(context or {})
        goal = self.create_goal(task)
        roles = list(goal.metadata.get("roles") or self.detect_roles(task))

        tasks: list[AgentTask] = []
        # Planning step first
        tasks.append(
            AgentTask(
                description=f"Plan approach for: {task[:200]}",
                agent="memory",
                priority=0.95,
                goal_id=goal.goal_id,
                payload={"phase": "plan", "context_keys": list(context.keys())},
            )
        )
        for i, role in enumerate(roles):
            if role == "memory":
                continue
            tasks.append(
                AgentTask(
                    description=f"{role} work: {task[:200]}",
                    agent=role,
                    priority=max(0.2, 0.9 - (i * 0.1)),
                    goal_id=goal.goal_id,
                    payload={"phase": "execute", "role": role},
                )
            )
        # Always end with quality
        if not any(t.agent == "quality" for t in tasks[1:]):
            tasks.append(
                AgentTask(
                    description=f"Quality review: {task[:160]}",
                    agent="quality",
                    priority=0.3,
                    goal_id=goal.goal_id,
                    payload={"phase": "review"},
                )
            )

        return {
            "goal": goal,
            "roles": roles,
            "tasks": tasks,
            "steps": [t.agent for t in tasks],
        }
