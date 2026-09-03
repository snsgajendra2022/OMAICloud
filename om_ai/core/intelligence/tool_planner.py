"""Decide which tools are needed from intent/capability — not keyword maps."""
from __future__ import annotations

from typing import Any


# Capability → default tools (registry)
CAPABILITY_TOOLS: dict[str, list[str]] = {
    "date": ["date"],
    "calculator": ["calculator"],
    "coding": ["code_execution", "file", "knowledge"],
    "prompt_generator": ["knowledge", "file"],
    "research": ["knowledge"],
    "recommendation": ["knowledge"],
    "planning": ["knowledge"],
    "analysis": ["knowledge"],
    "vision": ["vision", "ocr", "file"],
    "chat": [],
    "clarify": [],
}


class ToolPlanner:
    def plan(
        self,
        intent: dict[str, Any],
        capability: dict[str, Any],
        understanding: dict[str, Any],
    ) -> dict[str, Any]:
        cap = str(capability.get("capability") or "")
        tools = list(CAPABILITY_TOOLS.get(cap, []))
        action = str(understanding.get("action") or "")
        if action == "retrieve" and "date" not in tools and cap == "date":
            tools.append("date")
        if action == "calculate" and "calculator" not in tools:
            tools.append("calculator")
        return {
            "tools": tools,
            "need_date": "date" in tools,
            "need_calculator": "calculator" in tools,
            "need_file": "file" in tools,
            "need_code_execution": "code_execution" in tools,
            "need_knowledge": "knowledge" in tools,
        }
