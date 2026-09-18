"""STEP 26 — OM Autonomous Agent Runtime Layer."""
from __future__ import annotations

from om_ai.core.agent_runtime import (
    OMAutonomousAgentRuntime,
    run_agent_runtime,
)

__all__ = [
    "OMAutonomousAgentRuntime",
    "run_agent_runtime",
    "Step26AgentRuntime",
]


class Step26AgentRuntime(OMAutonomousAgentRuntime):
    """Alias for roadmap naming."""

    step = 26
