"""Agent civilization bridge — route to specialist agent roles."""
from __future__ import annotations

from typing import Any

_ROUTES = {
    "coding": "coding",
    "debug": "coding",
    "performance": "coding",
    "knowledge": "research",
    "agent": "master",
    "security": "security",
    "chat": "master",
}


def select_agents(intent: str, text: str = "") -> list[str]:
    t = (text or "").lower()
    agents = [_ROUTES.get(intent, "master")]
    if any(w in t for w in ("security", "auth", "vuln", "secret", "login")):
        agents.append("security")
    if any(w in t for w in ("deploy", "docker", "k8s", "ci", "production")):
        agents.append("deployment")
    if any(w in t for w in ("test", "pytest", "jest", "qa")):
        agents.append("testing")
    if any(w in t for w in ("sql", "schema", "postgres", "mysql", "mongo", "database")):
        agents.append("database")
    if any(w in t for w in ("robot", "motor", "gpio", "esp32", "sensor")):
        agents.append("hardware")
    seen: set[str] = set()
    out: list[str] = []
    for a in agents:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


def run_agents(goal: str, *, intent: str, agents: list[str], snippets: list[str] | None = None) -> dict[str, Any]:
    from om_ai.agents.specialists import run_specialists

    result = run_specialists(goal, agents=agents, snippets=snippets)
    notes = []
    try:
        from om_ai.agents.roles import ROLES

        for name in result.get("agents") or agents:
            role = ROLES.get(name)
            notes.append(f"{name}: {role.description}" if role else f"{name}: routed")
    except Exception:
        notes = [f"{a}: routed" for a in agents]
    result["notes"] = notes
    result["intent"] = intent
    return result
