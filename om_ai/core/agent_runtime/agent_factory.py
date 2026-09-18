"""Agent creation factory for STEP 26."""
from __future__ import annotations

from typing import Any

from om_ai.core.agents import (
    CodingAgent,
    KnowledgeAgent,
    MemoryAgent,
    QualityAgent,
    ResearchAgent,
    SecurityAgent,
)
from om_ai.core.agents.agent import Agent
from om_ai.core.agents.agent_registry import AgentRegistry
from om_ai.core.agents.base_agent import BaseAgent


_ROLE_CLASSES: dict[str, type] = {
    "coding": CodingAgent,
    "research": ResearchAgent,
    "knowledge": KnowledgeAgent,
    "quality": QualityAgent,
    "memory": MemoryAgent,
    "security": SecurityAgent,
}


class AgentFactory:
    """Create and register specialist / generic agents."""

    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self.registry = registry or AgentRegistry()

    def create(self, role: str, name: str | None = None) -> Any:
        role_key = (role or "general").strip().lower()
        agent_name = name or f"{role_key}_agent"

        cls = _ROLE_CLASSES.get(role_key)
        if cls is not None:
            agent = cls()
            # Ensure registry-compatible .name
            if not getattr(agent, "name", None):
                agent.name = agent_name
            else:
                # Keep specialty name for routing; also expose display name.
                agent.display_name = agent_name
        else:
            agent = Agent(name=agent_name, role=role_key)

        self.registry.register(agent)
        return agent

    def create_team(self, roles: list[str]) -> list[Any]:
        team = []
        for role in roles:
            team.append(self.create(role))
        return team

    def ensure_defaults(self) -> dict[str, Any]:
        """Bootstrap the standard OM specialist set."""
        created: dict[str, Any] = {}
        for role in ("coding", "research", "knowledge", "quality", "memory", "security"):
            if self.registry.get(role) is None and self.registry.get(f"{role}_agent") is None:
                agent = self.create(role, name=role)
                created[role] = agent
            else:
                created[role] = self.registry.get(role) or self.registry.get(f"{role}_agent")
        return created

    def get(self, name: str) -> Any:
        return self.registry.get(name)

    def list_agents(self) -> list[str]:
        return self.registry.list_agents()
