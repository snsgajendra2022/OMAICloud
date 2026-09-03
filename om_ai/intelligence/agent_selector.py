"""Dynamic agent selection from task requirements — not keyword→agent locks."""
from __future__ import annotations

from typing import Any


AGENT_CAPABILITIES: dict[str, dict[str, Any]] = {
    "coding": {
        "domains": {"software", "data", "architecture", "ai"},
        "actions": {"generate", "debug", "plan", "analyze", "create", "explain"},
        "intents": {"create", "debug", "create_prompt", "plan"},
    },
    "research": {
        "domains": {"science", "ai", "business", "general"},
        "actions": {"research", "explain", "compare", "summarize", "analyze"},
        "intents": {"research", "question", "compare", "summarize"},
    },
    "planning": {
        "domains": {"business", "software", "architecture", "general"},
        "actions": {"plan", "analyze"},
        "intents": {"plan", "analyze"},
    },
    "writing": {
        "domains": {"writing", "ai", "general", "software"},
        "actions": {"generate", "summarize"},
        "intents": {"create", "create_prompt", "generate", "summarize"},
    },
    "analysis": {
        "domains": {"business", "data", "science", "software"},
        "actions": {"analyze", "compare", "calculate"},
        "intents": {"analyze", "compare", "calculate"},
    },
    "general": {
        "domains": {"general", "music", "time", "writing"},
        "actions": {"chat", "recommend", "explain"},
        "intents": {"chat", "recommend", "datetime", "question"},
    },
}


class AgentSelector:
    def select(
        self,
        intent: dict[str, Any],
        understanding: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        domain = str(understanding.get("domain") or intent.get("domain") or "general")
        action = str(understanding.get("required_action") or "")
        intent_name = str(intent.get("intent") or "")
        complexity = str(understanding.get("complexity") or "medium")

        scores: dict[str, float] = {}
        for name, caps in AGENT_CAPABILITIES.items():
            score = 0.0
            if domain in caps["domains"]:
                score += 2.0
            if action in caps["actions"]:
                score += 1.5
            if intent_name in caps["intents"]:
                score += 1.5
            if name == "general":
                score += 0.2  # soft prior
            if complexity == "high" and name in {"coding", "planning", "analysis", "research"}:
                score += 0.5
            scores[name] = score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = ranked[0][0] if ranked else "general"
        secondary = [n for n, s in ranked[1:3] if s >= 1.0]

        # Prompt creation often needs writing + coding together
        if intent_name == "create_prompt" and "writing" not in ([primary] + secondary):
            secondary.insert(0, "writing")

        return {
            "primary": primary,
            "secondary": secondary,
            "scores": scores,
            "team": [primary] + [s for s in secondary if s != primary],
        }
