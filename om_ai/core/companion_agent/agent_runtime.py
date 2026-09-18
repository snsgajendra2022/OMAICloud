"""Companion agent runtime — planning loop with optional STEP 26 integration."""
from __future__ import annotations

import logging
from typing import Any

from om_ai.core.companion_security import SecurityContext

from .action_executor import CompanionActionExecutor
from .agent_session import AgentSession
from .cancellation_manager import CancellationManager
from .execution_verifier import ExecutionVerifier
from .goal import Goal
from .recovery_engine import RecoveryEngine
from .task import TaskStatus
from .task_graph import TaskGraph
from .task_planner import TaskPlanner
from .tool_selector import ToolSelector

logger = logging.getLogger(__name__)


class CompanionAgentRuntime:
    def __init__(self) -> None:
        self.planner = TaskPlanner()
        self.tools = ToolSelector()
        self.executor = CompanionActionExecutor()
        self.verifier = ExecutionVerifier()
        self.recovery = RecoveryEngine()
        self.cancellations = CancellationManager()

    def start_session(
        self, *, security: SecurityContext | None = None
    ) -> AgentSession:
        session_id, token = self.cancellations.create()
        session = AgentSession(session_id=session_id, cancel_token=token)
        session.security = security or SecurityContext(session_id=session_id)
        return session

    def run_goal(
        self,
        session: AgentSession,
        goal: Goal,
        *,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session.goals.append(goal)
        runtime_pack = self.planner.enrich_with_agent_runtime(goal, context=context)
        if runtime_pack:
            session.metadata["agent_runtime"] = runtime_pack

        for task in self.planner.plan_from_goal(goal):
            cap = self.tools.select_capability(task)
            if cap:
                task.capability = cap
            session.graph.add(task)

        return self.run_graph(session)

    def run_graph(self, session: AgentSession) -> dict[str, Any]:
        graph = session.graph
        ctx = session.context()
        token = session.cancel_token

        while True:
            if token and token.is_cancelled:
                return {"status": "cancelled", "session_id": session.session_id}

            ready = graph.ready_tasks()
            if not ready:
                pending = [
                    t
                    for t in graph.all_tasks()
                    if t.status
                    in {TaskStatus.PENDING, TaskStatus.READY, TaskStatus.RUNNING}
                ]
                if not pending:
                    break
                if any(t.status == TaskStatus.FAILED for t in graph.all_tasks()):
                    break
                raise RuntimeError("deadlock: tasks waiting on failed dependencies")

            for task in ready:
                if token:
                    token.raise_if_cancelled()
                task.status = TaskStatus.RUNNING
                task.touch()
                try:
                    output = self.executor.execute_task(ctx, task)
                    ok, reason = self.verifier.verify(task, output)
                    if not ok:
                        task.status = TaskStatus.FAILED
                        task.error = reason
                        if self.recovery.should_retry(task):
                            self.recovery.prepare_retry(task)
                    else:
                        task.status = TaskStatus.SUCCEEDED
                except Exception as exc:
                    logger.exception("task failed: %s", task.task_id)
                    task.status = TaskStatus.FAILED
                    task.error = str(exc)
                    if self.recovery.should_retry(task):
                        self.recovery.prepare_retry(task)

        succeeded = sum(
            1 for t in graph.all_tasks() if t.status == TaskStatus.SUCCEEDED
        )
        failed = sum(1 for t in graph.all_tasks() if t.status == TaskStatus.FAILED)
        return {
            "session_id": session.session_id,
            "goal_id": session.goals[-1].goal_id if session.goals else None,
            "tasks": len(graph.all_tasks()),
            "succeeded": succeeded,
            "failed": failed,
            "status": "ok" if failed == 0 else "partial",
        }
