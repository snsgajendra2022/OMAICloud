"""Route classified intents to agents / pipelines."""
from __future__ import annotations

from typing import Any

from .classifier import IntentClassification, classify


AGENT_MAP = {
    "coding": "coding",
    "debug": "coding",
    "architecture": "coding",
    "research": "research",
    "business": "business",
    "general": "master",
}


def route(text: str | IntentClassification) -> dict[str, Any]:
    c = text if isinstance(text, IntentClassification) else classify(str(text))
    agent = AGENT_MAP.get(c.intent, c.agent or "master")
    pipeline = "reasoning"
    if agent == "coding":
        pipeline = "coding_brain"
    elif agent == "research":
        pipeline = "knowledge+reasoning"
    return {
        "agent": agent,
        "pipeline": pipeline,
        "intent": c.to_dict(),
        "next": [
            "Retrieve knowledge / memory",
            "Run selected agent",
            "Verify quality / security",
            "Return formatted response",
        ],
    }
