"""OM Agent role registry — Master + specialist agents (thin definitions)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentRole:
    name: str
    capabilities: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "capabilities": self.capabilities,
            "description": self.description,
        }


ROLES: dict[str, AgentRole] = {
    "master": AgentRole(
        "master",
        ["route", "plan", "delegate", "verify"],
        "OM Master orchestrator",
    ),
    "coding": AgentRole(
        "coding",
        ["read_repo", "understand_files", "create_code", "modify_code", "run_tests", "debug"],
        "Software engineering agent",
    ),
    "research": AgentRole(
        "research",
        ["analyze_papers", "reports", "compare_tech", "summarize"],
        "Research agent",
    ),
    "database": AgentRole(
        "database",
        ["schema", "queries", "migrations", "performance"],
        "Database agent",
    ),
    "security": AgentRole(
        "security",
        ["review", "threats", "secrets", "sandbox"],
        "Security agent",
    ),
    "testing": AgentRole(
        "testing",
        ["test_plan", "regression", "edge_cases", "ci"],
        "Testing agent",
    ),
    "deployment": AgentRole(
        "deployment",
        ["docker", "compose", "env", "health", "tls"],
        "Deployment agent",
    ),
    "devops": AgentRole(
        "devops",
        ["ci", "deploy", "containers", "observability"],
        "DevOps / deployment agent",
    ),
    "business": AgentRole(
        "business",
        ["strategy", "markets", "ops", "reporting"],
        "Business agent",
    ),
    "science": AgentRole(
        "science",
        ["physics", "biology", "chemistry", "math"],
        "Science agent",
    ),
    "hardware": AgentRole(
        "hardware",
        ["electronics", "sensors", "embedded"],
        "Hardware agent",
    ),
    "robotics": AgentRole(
        "robotics",
        ["control", "perception", "planning", "sim"],
        "Robotics agent",
    ),
}


def list_agents() -> list[dict[str, Any]]:
    return [r.to_dict() for r in ROLES.values()]


def select_agent(goal: str) -> dict[str, Any]:
    from om_ai.core.intent_engine import classify, route

    c = classify(goal)
    r = route(c)
    name = r.get("agent") or "master"
    role = ROLES.get(name) or ROLES["master"]
    return {"selected": role.to_dict(), "routing": r}
