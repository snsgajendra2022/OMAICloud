"""STEP 26 — OM Autonomous Agent Runtime Layer.

Provides:
  - Agent creation
  - Agent memory
  - Agent goals
  - Agent task queue
  - Agent collaboration
  - Agent communication
  - Agent planning
  - Agent execution loop
"""
from __future__ import annotations

from .agent_goal import AgentGoal
from .autonomous_runtime import (
    OMAutonomousAgentRuntime,
    run_agent_runtime,
)
from .task_queue import AgentTask, AgentTaskQueue

__all__ = [
    "AgentGoal",
    "AgentTask",
    "AgentTaskQueue",
    "OMAutonomousAgentRuntime",
    "run_agent_runtime",
]
