"""Named production workflows."""
from __future__ import annotations

from typing import Any

from ai_platform.orchestration import OrchestrationPlatform


WORKFLOWS = {
    "standard_intelligence": [
        "intent",
        "plan",
        "retrieve",
        "execute",
        "verify",
        "quality",
        "respond",
    ],
    "coding": [
        "intent",
        "repo_map",
        "plan",
        "generate",
        "test_suggest",
        "security_review",
        "respond",
    ],
}


def run_workflow(name: str, request: str, **kwargs: Any) -> dict[str, Any]:
    # All workflows currently execute via orchestration engine; name is recorded.
    result = OrchestrationPlatform().execute(request, **kwargs)
    result["workflow"] = name
    result["declared_steps"] = WORKFLOWS.get(name, WORKFLOWS["standard_intelligence"])
    return result
