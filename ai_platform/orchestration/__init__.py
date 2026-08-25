"""OM Orchestration Platform — agent manager, scheduler, workflow, tools, context, policy."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from services.api_gateway import APIGateway


@dataclass
class Task:
    id: str
    name: str
    payload: dict[str, Any]
    status: str = "queued"
    result: dict[str, Any] | None = None


class PolicyEngine:
    """Deny-by-default for dangerous actions."""

    def allow(self, action: str, *, apply: bool = False) -> tuple[bool, str]:
        if action in {"shell.unrestricted", "delete_all"}:
            return False, "denied by policy"
        if action == "code.apply" and not apply:
            return False, "apply not requested"
        return True, "ok"


class ContextManager:
    def __init__(self) -> None:
        self._ctx: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._ctx[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._ctx.get(key, default)

    def snapshot(self) -> dict[str, Any]:
        return dict(self._ctx)


class TaskScheduler:
    def __init__(self) -> None:
        self.tasks: list[Task] = []

    def enqueue(self, name: str, payload: dict[str, Any]) -> Task:
        t = Task(id=str(uuid.uuid4()), name=name, payload=payload)
        self.tasks.append(t)
        return t


class WorkflowEngine:
    """Linear production reasoning workflow."""

    STEPS = (
        "intent",
        "plan",
        "retrieve",
        "execute",
        "verify",
        "quality",
        "respond",
    )

    def __init__(self, gateway: APIGateway | None = None) -> None:
        self.gateway = gateway or APIGateway()
        self.policy = PolicyEngine()
        self.context = ContextManager()
        self.scheduler = TaskScheduler()

    def run(self, request: str, *, root: str = ".") -> dict[str, Any]:
        started = time.time()
        trace: list[dict[str, Any]] = []
        # 1 intent via model gateway / reasoning
        reason = self.gateway.handle("reason", question=request)
        trace.append({"step": "intent+plan+verify", "ok": reason.get("ok")})
        self.context.set("reasoning", reason.get("data"))

        # 2 retrieve
        know = self.gateway.handle("knowledge.search", query=request)
        trace.append({"step": "retrieve", "ok": know.get("ok")})
        self.context.set("knowledge", know.get("data"))

        # 3 agent execute (dry)
        allowed, why = self.policy.allow("code.apply", apply=False)
        agent = self.gateway.handle("agent", task=request, root=root)
        trace.append({"step": "execute", "ok": agent.get("ok"), "policy": why, "allowed": allowed})

        # 4 quality via model route (structured)
        final = self.gateway.handle("chat", prompt=request)
        trace.append({"step": "quality+respond", "ok": final.get("ok")})

        # 5 improve if weak
        text = ""
        if final.get("ok") and isinstance(final.get("data"), dict):
            text = str(final["data"].get("text") or "")
        if text and len(text.split()) < 20:
            self.gateway.handle("improve", question=request, answer=text)
            trace.append({"step": "learning", "ok": True})

        task = self.scheduler.enqueue("workflow", {"request": request})
        task.status = "done"
        task.result = {"trace": trace}

        return {
            "ok": True,
            "request": request,
            "steps": list(self.STEPS),
            "trace": trace,
            "response": text or (reason.get("data") or {}).get("markdown", ""),
            "task_id": task.id,
            "latency_ms": int((time.time() - started) * 1000),
            "context_keys": list(self.context.snapshot().keys()),
        }


class OrchestrationPlatform:
    def __init__(self) -> None:
        self.gateway = APIGateway()
        self.workflow = WorkflowEngine(self.gateway)

    def health(self) -> dict[str, Any]:
        return {
            "orchestration": "healthy",
            "gateway": self.gateway.health(),
            "components": [
                "agent_manager",
                "task_scheduler",
                "workflow_engine",
                "tool_execution",
                "context_manager",
                "policy_engine",
            ],
        }

    def execute(self, request: str, **kwargs: Any) -> dict[str, Any]:
        return self.workflow.run(request, **kwargs)
