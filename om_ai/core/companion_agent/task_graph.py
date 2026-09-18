"""Task graph with dependency ordering."""
from __future__ import annotations

from collections import deque

from .task import Task, TaskStatus


class TaskGraph:
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def add(self, task: Task) -> None:
        self._tasks[task.task_id] = task

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def all_tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def ready_tasks(self) -> list[Task]:
        ready: list[Task] = []
        for task in self._tasks.values():
            if task.status not in {TaskStatus.PENDING, TaskStatus.READY}:
                continue
            if self._deps_satisfied(task):
                task.status = TaskStatus.READY
                ready.append(task)
        return ready

    def _deps_satisfied(self, task: Task) -> bool:
        for dep_id in task.depends_on:
            dep = self._tasks.get(dep_id)
            if dep is None or dep.status != TaskStatus.SUCCEEDED:
                return False
        return True

    def topological_order(self) -> list[Task]:
        indegree: dict[str, int] = {tid: 0 for tid in self._tasks}
        for task in self._tasks.values():
            for dep in task.depends_on:
                if dep in indegree:
                    indegree[task.task_id] += 1
        q: deque[str] = deque(t for t, d in indegree.items() if d == 0)
        order: list[Task] = []
        while q:
            tid = q.popleft()
            order.append(self._tasks[tid])
            for task in self._tasks.values():
                if tid in task.depends_on:
                    indegree[task.task_id] -= 1
                    if indegree[task.task_id] == 0:
                        q.append(task.task_id)
        if len(order) != len(self._tasks):
            raise ValueError("task graph contains a cycle")
        return order

    def mark_cancelled_recursive(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        task.status = TaskStatus.CANCELLED
        task.touch()
        for t in self._tasks.values():
            if task_id in t.depends_on and t.status == TaskStatus.PENDING:
                self.mark_cancelled_recursive(t.task_id)
