"""Plan tasks from goals; optionally consult agent runtime."""
from __future__ import annotations

import logging
from typing import Any

from .goal import Goal
from .task import Task

logger = logging.getLogger(__name__)


class TaskPlanner:
    def plan_from_goal(self, goal: Goal) -> list[Task]:
        desc = goal.description.strip()
        tasks: list[Task] = [
            Task(
                description=f"Analyze goal: {desc}",
                goal_id=goal.goal_id,
                capability=None,
            ),
            Task(
                description=f"Execute goal: {desc}",
                goal_id=goal.goal_id,
                depends_on=(),
            ),
            Task(
                description=f"Verify goal: {desc}",
                goal_id=goal.goal_id,
            ),
        ]
        if len(tasks) >= 2:
            tasks[2].depends_on = (tasks[1].task_id,)
            tasks[1].depends_on = (tasks[0].task_id,)
        return tasks

    def enrich_with_agent_runtime(
        self, goal: Goal, *, context: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        try:
            from om_ai.core.agent_runtime import run_agent_runtime

            pack = run_agent_runtime(goal.description, context=context or {})
            return pack if isinstance(pack, dict) else {"pack": pack}
        except Exception as exc:
            logger.warning("run_agent_runtime unavailable: %s", exc)
            return None
