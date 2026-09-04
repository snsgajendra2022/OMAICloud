"""Decide which tools are needed — delegates to STEP 86 ToolDecisionEngine."""
from __future__ import annotations

from typing import Any

# Capability → default tools (registry) — kept for back-compat
CAPABILITY_TOOLS: dict[str, list[str]] = {
    "date": ["date"],
    "calculator": ["calculator"],
    "coding": ["code_execution", "knowledge", "file"],
    "prompt_generator": ["knowledge"],
    "research": ["knowledge"],
    "recommendation": ["knowledge"],
    "planning": ["knowledge"],
    "analysis": ["knowledge"],
    "vision": ["vision", "ocr"],
    "chat": [],
    "clarify": [],
}


class ToolPlanner:
    def plan(
        self,
        intent: dict[str, Any],
        capability: dict[str, Any],
        understanding: dict[str, Any],
        *,
        question: str = "",
    ) -> dict[str, Any]:
        q = question or str(understanding.get("text") or understanding.get("query") or "")
        try:
            from om_ai.tools.intelligence import ToolDecisionEngine

            decision = ToolDecisionEngine().decide(
                q,
                intent=intent,
                capability=capability,
                understanding=understanding,
            )
            tools = list(decision.tools)
            return {
                "tools": tools,
                "need_date": "date" in tools,
                "need_calculator": "calculator" in tools,
                "need_file": "file" in tools,
                "need_code_execution": "code_execution" in tools,
                "need_knowledge": "knowledge" in tools,
                "need_web": "web" in tools,
                "mode": decision.mode,
                "risk": decision.risk,
                "reason": decision.reason,
                "confidence": decision.confidence,
            }
        except Exception:
            cap = str(capability.get("capability") or "")
            tools = list(CAPABILITY_TOOLS.get(cap, []))
            action = str(understanding.get("action") or "")
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
