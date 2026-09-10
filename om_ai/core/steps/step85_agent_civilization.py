"""STEP 85 — Autonomous Agent Civilization.

Mission planning → specialist agents → communication → evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentSpec:
    name: str
    role: str
    skills: list[str] = field(default_factory=list)


@dataclass
class Mission:
    goal: str
    agents: list[AgentSpec] = field(default_factory=list)
    tasks: list[dict[str, Any]] = field(default_factory=list)
    status: str = "planned"


class AgentCivilization:
    ROSTER = [
        AgentSpec("planner", "Project Manager", ["decompose", "prioritize"]),
        AgentSpec("research", "Research Agent", ["search", "verify", "cite"]),
        AgentSpec("frontend", "Frontend Agent", ["ui", "react", "css"]),
        AgentSpec("backend", "Backend Agent", ["api", "auth", "services"]),
        AgentSpec("database", "Database Agent", ["schema", "sql", "indexing"]),
        AgentSpec("qa", "Testing Agent", ["tests", "edge-cases"]),
        AgentSpec("security", "Security Agent", ["threats", "authz"]),
        AgentSpec("review", "Review Agent", ["critique", "quality"]),
        AgentSpec("deploy", "Deployment Agent", ["ci", "release"]),
        AgentSpec("coordinator", "Coordinator Agent", ["merge", "schedule"]),
    ]

    def plan_mission(self, goal: str) -> Mission:
        g = (goal or "").strip()
        low = g.lower()
        needed = ["planner", "coordinator"]
        if any(w in low for w in ("build", "app", "ecommerce", "website", "system")):
            needed += ["frontend", "backend", "database", "qa", "security", "review", "deploy"]
        if any(w in low for w in ("research", "latest", "compare", "why")):
            needed += ["research", "review"]
        if any(w in low for w in ("code", "bug", "api", "react", "python")):
            needed += ["backend", "qa", "review"]
        if any(w in low for w in ("architect", "design", "scale", "uber")):
            needed += ["planner", "backend", "database", "security", "review"]

        selected = []
        seen = set()
        for a in self.ROSTER:
            if a.name in needed and a.name not in seen:
                selected.append(a)
                seen.add(a.name)

        tasks = []
        for i, agent in enumerate(selected, 1):
            tasks.append(
                {
                    "id": i,
                    "agent": agent.name,
                    "role": agent.role,
                    "instruction": f"{agent.role}: contribute to '{g}' using {', '.join(agent.skills) or 'general skills'}.",
                    "status": "queued",
                }
            )
        return Mission(goal=g, agents=selected, tasks=tasks, status="planned")

    def run(self, goal: str) -> dict[str, Any]:
        mission = self.plan_mission(goal)
        results = []
        messages = []
        for task in mission.tasks:
            agent = task["agent"]
            output = self._execute_task(goal, task)
            task["status"] = "done"
            task["output"] = output
            results.append(task)
            messages.append(
                {
                    "from": agent,
                    "to": "coordinator",
                    "content": output[:500],
                }
            )
        mission.status = "complete"
        summary = self._coordinate(goal, results)
        return {
            "step": 85,
            "status": mission.status,
            "goal": mission.goal,
            "agents": [a.name for a in mission.agents],
            "tasks": results,
            "messages": messages,
            "summary": summary,
        }

    def _execute_task(self, goal: str, task: dict[str, Any]) -> str:
        agent = task["agent"]
        role = task["role"]
        templates = {
            "planner": f"Break '{goal}' into milestones: discovery, design, build, test, launch.",
            "research": f"Gather requirements and comparable systems for '{goal}'.",
            "frontend": "Define UI surfaces, components, routing, and state management.",
            "backend": "Define APIs, auth, services, and integration contracts.",
            "database": "Propose entities, relationships, indexes, and consistency model.",
            "qa": "List test plan: unit, integration, e2e, and failure scenarios.",
            "security": "Cover authn/authz, input validation, secrets, and abuse cases.",
            "review": "Review for completeness, risks, and missing acceptance criteria.",
            "deploy": "Outline CI/CD, environments, rollback, and monitoring.",
            "coordinator": "Merge specialist outputs into one delivery plan.",
        }
        return templates.get(agent, f"{role} analyzed: {goal}")

    def _coordinate(self, goal: str, results: list[dict[str, Any]]) -> str:
        lines = [f"Agent civilization plan for: {goal}", ""]
        for t in results:
            lines.append(f"- {t['role']}: {t.get('output', '')}")
        lines.append("")
        lines.append("Coordinator: sequence as Planner → Research/Design → Build → QA/Security → Review → Deploy.")
        return "\n".join(lines)
