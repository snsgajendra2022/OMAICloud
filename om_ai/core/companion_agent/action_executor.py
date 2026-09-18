"""Execute capability tasks via device + action control layers."""
from __future__ import annotations

from typing import Any

from om_ai.core.action_control import ActionRequest, RiskClass
from om_ai.core.companion_security import SecurityContext
from om_ai.core.device_runtime import DeviceRuntime

from .task import Task, TaskStatus


class CompanionActionExecutor:
    def __init__(
        self,
        *,
        device_runtime: DeviceRuntime | None = None,
    ) -> None:
        self.device = device_runtime or DeviceRuntime()

    def execute_task(self, ctx: SecurityContext, task: Task) -> Any:
        if not task.capability:
            task.status = TaskStatus.SUCCEEDED
            task.result = {"note": "analysis-only task", "description": task.description}
            task.touch()
            return task.result

        request = ActionRequest(
            action_type=task.capability,
            risk_class=_risk_from_capability(task.capability),
            parameters=dict(task.parameters),
            actor=ctx.actor,
            source="external" if ctx.is_external_content else "internal",
            correlation_id=task.task_id,
        )

        ok, reason = self.device.security.guard_action(ctx, request)
        if not ok:
            task.status = TaskStatus.FAILED
            task.error = reason
            task.touch()
            raise PermissionError(reason)

        result = self.device.invoke(ctx, task.capability, task.parameters)
        task.status = TaskStatus.SUCCEEDED
        task.result = result
        task.touch()
        return result


def _risk_from_capability(capability: str) -> RiskClass:
    if ".read" in capability or capability.endswith(".list"):
        return RiskClass.READ_ONLY
    if capability == "system.notification":
        return RiskClass.LOW_IMPACT
    if "delete" in capability or capability == "process.stop":
        return RiskClass.DESTRUCTIVE
    if capability.startswith("filesystem."):
        return RiskClass.REVERSIBLE_WRITE
    return RiskClass.EXTERNAL_SIDE_EFFECT
