"""Runtime agent memory (wraps core AgentMemory + episode store)."""
from __future__ import annotations

from typing import Any

from om_ai.core.agents.agent_memory import AgentMemory


class RuntimeAgentMemory:
    """Per-agent + shared episodic memory for the execution loop."""

    def __init__(self) -> None:
        self._core = AgentMemory()
        self._episodes: list[dict[str, Any]] = []
        self._goals: dict[str, list[str]] = {}

    def remember(self, agent: str, data: Any) -> None:
        self._core.remember(agent, data)

    def recall(self, agent: str) -> list[Any]:
        return list(self._core.recall(agent) or [])

    def remember_goal(self, agent: str, goal_id: str) -> None:
        self._goals.setdefault(agent, []).append(goal_id)

    def goals_for(self, agent: str) -> list[str]:
        return list(self._goals.get(agent) or [])

    def add_episode(self, episode: dict[str, Any]) -> None:
        self._episodes.append(dict(episode))
        if len(self._episodes) > 200:
            self._episodes = self._episodes[-200:]

    def recent_episodes(self, limit: int = 10) -> list[dict[str, Any]]:
        return list(self._episodes[-limit:])

    def snapshot(self) -> dict[str, Any]:
        return {
            "agents": {
                name: list(items)
                for name, items in getattr(self._core, "storage", {}).items()
            },
            "episodes": self.recent_episodes(20),
            "goals": dict(self._goals),
        }
