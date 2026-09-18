"""Simple recovery strategies for failed tasks."""
from __future__ import annotations

from .task import Task, TaskStatus


class RecoveryEngine:
    def __init__(self, *, max_retries: int = 2) -> None:
        self.max_retries = max_retries
        self._attempts: dict[str, int] = {}

    def should_retry(self, task: Task) -> bool:
        count = self._attempts.get(task.task_id, 0)
        return task.status == TaskStatus.FAILED and count < self.max_retries

    def prepare_retry(self, task: Task) -> None:
        self._attempts[task.task_id] = self._attempts.get(task.task_id, 0) + 1
        task.status = TaskStatus.READY
        task.error = None
        task.touch()
