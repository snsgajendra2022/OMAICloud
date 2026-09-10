"""STEP 87 marker — Research Intelligence (already implemented under core/research)."""
from __future__ import annotations

from om_ai.core.research import ResearchEngine
from om_ai.core.intelligence.freshness_detector import FreshnessDetector


class ResearchIntelligence:
    """Facade confirming STEP 87 completion."""

    def __init__(self) -> None:
        self.engine = ResearchEngine()
        self.freshness = FreshnessDetector()

    def run(self, message: str, understanding: dict | None = None) -> dict:
        fresh = self.freshness.analyze(message)
        state = None
        if fresh.get("requires_research"):
            state = self.engine.research(message, understanding=understanding)
        return {
            "step": 87,
            "status": "complete",
            "freshness": fresh,
            "research_status": getattr(state, "status", None),
            "sources": len(getattr(state, "sources", []) or []) if state else 0,
            "citations": list(getattr(state, "citations", []) or []) if state else [],
            "summary_context": getattr(state, "summary_context", "") if state else "",
        }
