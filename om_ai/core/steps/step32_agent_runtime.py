"""STEP 32 — OM Agent Runtime (production facade over agent_runtime)."""
from __future__ import annotations

from om_ai.core.agent_runtime import OMAutonomousAgentRuntime, run_agent_runtime

__all__ = ["OMAutonomousAgentRuntime", "run_agent_runtime", "Step32AgentRuntime"]


class Step32AgentRuntime(OMAutonomousAgentRuntime):
    step = 32
