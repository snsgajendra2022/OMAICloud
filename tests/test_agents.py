"""Agent execute(question, context) contract tests."""
from __future__ import annotations

from om_ai.agents.coding_agent import CodingAgent
from om_ai.agents.research_agent import ResearchAgent
from om_ai.agents.general_agent import GeneralAgent
from om_ai.agents.router import AgentRouter


def test_agents_implement_execute():
    for cls in (CodingAgent, ResearchAgent, GeneralAgent):
        agent = cls()
        out = agent.execute("explain this", {"memory": {}})
        assert out is not None
        assert isinstance(out, dict)


def test_router_selects_coding_for_laravel():
    routed = AgentRouter().route("create Laravel authentication API")
    assert routed["name"] == "coding"
    assert routed["score"] >= 0.5
