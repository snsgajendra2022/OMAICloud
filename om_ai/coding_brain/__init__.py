"""Coding brain — language/framework skills + coding agent facade."""
from __future__ import annotations

from typing import Any

LANGUAGES = [
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "C#",
    "PHP",
    "Go",
    "Rust",
    "SQL",
]

FRAMEWORKS = [
    "React",
    "Next.js",
    "Angular",
    "Vue",
    "FastAPI",
    "Django",
    "Laravel",
    "Spring Boot",
    ".NET",
    "Express",
]

FEATURES = [
    "code_generation",
    "code_explanation",
    "bug_fixing",
    "architecture_design",
    "security_review",
    "testing",
]


def catalog() -> dict[str, Any]:
    return {"languages": LANGUAGES, "frameworks": FRAMEWORKS, "features": FEATURES}


def handle(task: str, *, root: str = ".", dry_run: bool = True) -> dict[str, Any]:
    from om_ai.agent.coding_agent import plan_coding_task
    from om_ai.core.intent_engine import classify
    from om_ai.core.reasoning.pipeline import run_reasoning_pipeline

    intent = classify(task)
    reason = run_reasoning_pipeline(task, retrieve=True)
    plan = plan_coding_task(task, root=root, dry_run=dry_run)
    return {
        "intent": intent.to_dict(),
        "catalog": catalog(),
        "reasoning_markdown": reason.get("markdown"),
        "plan": plan,
        "dry_run": dry_run,
    }
