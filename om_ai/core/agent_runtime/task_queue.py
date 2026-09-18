"""Agent task queue for STEP 26 runtime."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


@dataclass
class AgentTask:
    """One unit of work on the agent queue."""

    description: str
    agent: str = "general"
    priority: float = 0.5
    status: str = "pending"  # pending | running | done | failed
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    goal_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "agent": self.agent,
            "priority": self.priority,
            "status": self.status,
            "goal_id": self.goal_id,
            "payload": dict(self.payload),
            "result": self.result,
            "created_at": self.created_at,
        }


class AgentTaskQueue:
    """Priority-aware FIFO task queue."""

    def __init__(self) -> None:
        self._pending: deque[AgentTask] = deque()
        self._history: list[AgentTask] = []

    def enqueue(self, task: AgentTask) -> AgentTask:
        # Higher priority inserts closer to the front among equals.
        items = list(self._pending)
        items.append(task)
        items.sort(key=lambda t: (-float(t.priority), t.created_at))
        self._pending = deque(items)
        return task

    def dequeue(self) -> AgentTask | None:
        if not self._pending:
            return None
        task = self._pending.popleft()
        task.status = "running"
        return task

    def complete(self, task: AgentTask, result: Any = None) -> AgentTask:
        task.status = "done"
        task.result = result
        self._history.append(task)
        return task

    def fail(self, task: AgentTask, error: str) -> AgentTask:
        task.status = "failed"
        task.result = {"error": error}
        self._history.append(task)
        return task

    def pending(self) -> list[AgentTask]:
        return list(self._pending)

    def history(self) -> list[AgentTask]:
        return list(self._history)

    def size(self) -> int:
        return len(self._pending)

    def clear(self) -> None:
        self._pending.clear()
