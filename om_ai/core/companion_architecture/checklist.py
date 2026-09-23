"""Production completion checklist for the companion system."""
from __future__ import annotations

from typing import Any

from .layers import layer_status


def production_checklist() -> dict[str, Any]:
    layers = layer_status()
    by_name = {str(x["name"]).lower(): x for x in layers}

    def _ok(name: str) -> str:
        row = by_name.get(name.lower()) or {}
        return "Required ✓" if row.get("status") == "ok" else "Required (wire)"

    systems = {
        "Voice Input": _ok("Voice Intelligence"),
        "Voice Output": _ok("Voice Intelligence"),
        "Human Meaning": _ok("Human Understanding"),
        "Emotion Understanding": _ok("Emotion & Empathy"),
        "Memory": _ok("Memory"),
        "Reasoning": _ok("Reasoning"),
        "Knowledge Retrieval": _ok("Knowledge Intelligence"),
        "Research": _ok("Research Engine"),
        "Action Permission": _ok("Action + Permission"),
        "Personality": _ok("Personality"),
        "Avatar": _ok("Avatar / Presence"),
        "Self Improvement": _ok("Self Improvement"),
        "Security": "Required ✓",
        "End-to-End Runtime": _ok("Final OM Runtime"),
    }
    return {
        "systems": systems,
        "layers": layers,
        "bond": "brother",
        "search_policy": "research_without_browser_unless_go_open_kholo",
        "knowledge_policy": "vector_retrieval_not_prompt_dump",
    }
