"""Agent microservice — wraps AgentRuntime + roles."""
from __future__ import annotations

from typing import Any

from services._common import ServiceHealth, ok


class AgentService:
    def health(self) -> dict[str, Any]:
        from om_ai.agents.roles import list_agents

        return ServiceHealth("agent-service", detail={"agents": len(list_agents())}).to_dict()

    def run(self, task: str, *, root: str = ".", apply: bool = False) -> dict[str, Any]:
        from om_ai.agents.runtime import run_agent

        return ok(run_agent(task, root=root, apply=apply))
