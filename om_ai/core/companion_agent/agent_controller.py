"""High-level controller for companion agent sessions."""
from __future__ import annotations

from typing import Any

from om_ai.core.companion_security import SecurityContext

from .agent_runtime import CompanionAgentRuntime
from .agent_session import AgentSession
from .goal import Goal


class AgentController:
    def __init__(self, runtime: CompanionAgentRuntime | None = None) -> None:
        self.runtime = runtime or CompanionAgentRuntime()

    def run(
        self,
        user_goal: str,
        *,
        security: SecurityContext | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session = self.runtime.start_session(security=security)
        goal = Goal(description=user_goal)
        return self.runtime.run_goal(session, goal, context=context)

    def cancel(self, session: AgentSession) -> bool:
        return self.runtime.cancellations.cancel(session.session_id)
