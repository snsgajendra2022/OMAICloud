"""Agent execution loop for STEP 26."""
from __future__ import annotations

from typing import Any, Callable

from .communication import RuntimeCommunication
from .runtime_memory import RuntimeAgentMemory
from .task_queue import AgentTask, AgentTaskQueue


class AgentExecutionLoop:
    """Drain the task queue: plan → execute → remember → communicate."""

    def __init__(
        self,
        queue: AgentTaskQueue,
        memory: RuntimeAgentMemory,
        communication: RuntimeCommunication,
        *,
        max_steps: int = 12,
    ) -> None:
        self.queue = queue
        self.memory = memory
        self.communication = communication
        self.max_steps = max_steps

    def run(
        self,
        *,
        executor: Callable[[AgentTask], Any],
        on_step: Callable[[AgentTask, Any], None] | None = None,
    ) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        steps = 0
        errors: list[str] = []

        while steps < self.max_steps:
            task = self.queue.dequeue()
            if task is None:
                break
            steps += 1
            try:
                out = executor(task)
                self.queue.complete(task, out)
                self.memory.remember(
                    task.agent,
                    {
                        "task_id": task.task_id,
                        "description": task.description,
                        "result": out,
                    },
                )
                self.communication.send(
                    task.agent,
                    "orchestrator",
                    f"Completed {task.task_id}",
                    kind="result",
                )
                if on_step:
                    on_step(task, out)
                results.append(
                    {
                        "task_id": task.task_id,
                        "agent": task.agent,
                        "status": "done",
                        "result": out,
                    }
                )
            except Exception as exc:
                self.queue.fail(task, str(exc))
                errors.append(f"{task.agent}:{exc}")
                results.append(
                    {
                        "task_id": task.task_id,
                        "agent": task.agent,
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        self.memory.add_episode(
            {
                "steps": steps,
                "completed": sum(1 for r in results if r.get("status") == "done"),
                "failed": len(errors),
            }
        )
        return {
            "steps": steps,
            "results": results,
            "errors": errors,
            "pending": self.queue.size(),
            "ok": not errors,
        }
