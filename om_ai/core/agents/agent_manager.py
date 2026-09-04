from .agent_registry import AgentRegistry
from .team_builder import TeamBuilder


class AgentManager:
    def __init__(self):
        self.registry = AgentRegistry()
        self.team_builder = TeamBuilder()

    def create_team(self, task):
        return self.team_builder.create_team(task)

    def available_agents(self):
        return self.registry.list_agents()

    def route(self, task: str):
        """Route a task to the best available agent / team (connected to chat)."""
        agents = []
        try:
            agents = list(self.available_agents() or [])
        except Exception:
            agents = []
        team = None
        try:
            team = self.create_team(task)
        except Exception:
            team = None
        low = (task or "").lower()
        specialty = "general"
        if any(w in low for w in ("code", "bug", "python", "react")):
            specialty = "coding"
        elif any(w in low for w in ("research", "search", "explain")):
            specialty = "research"
        elif any(w in low for w in ("test", "qa")):
            specialty = "testing"
        elif any(w in low for w in ("security", "auth", "threat")):
            specialty = "security"
        return {
            "specialty": specialty,
            "agents": agents,
            "team": team,
            "task": (task or "")[:200],
        }
