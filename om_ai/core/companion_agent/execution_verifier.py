"""Verify task postconditions after execution."""
from __future__ import annotations

from typing import Any

from .task import Task, TaskStatus


class ExecutionVerifier:
    def verify(self, task: Task, output: Any) -> tuple[bool, str]:
        if task.status == TaskStatus.CANCELLED:
            return False, "task cancelled"

        expected = task.postconditions or {}
        if not expected:
            if output is None and task.capability:
                return False, "expected non-null output for capability task"
            return True, ""

        if "non_empty" in expected and expected["non_empty"]:
            if output is None or output == "" or output == {}:
                return False, "output empty"

        if "contains" in expected:
            needle = str(expected["contains"])
            if needle not in str(output):
                return False, f"output missing {needle!r}"

        if "returncode" in expected and isinstance(output, dict):
            if output.get("returncode") != expected["returncode"]:
                return False, "unexpected returncode"

        return True, ""
