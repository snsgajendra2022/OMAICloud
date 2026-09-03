"""Route to knowledge *sources* by domain — never spawn MusicAgent/DateAgent/etc."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


# Domain → knowledge source labels (expandable registry, not if/else answer map)
DOMAIN_SOURCES: dict[str, list[str]] = {
    "music": ["recommendation_knowledge", "lifestyle_knowledge"],
    "software": ["code_knowledge", "documentation_knowledge", "architecture_patterns"],
    "ai": ["ai_research_knowledge", "prompt_knowledge"],
    "business": ["business_knowledge", "strategy_knowledge"],
    "science": ["science_knowledge", "explanatory_knowledge"],
    "time": ["calendar_clock"],
    "writing": ["writing_knowledge"],
    "data": ["data_knowledge", "schema_patterns"],
    "architecture": ["architecture_patterns", "system_design_knowledge"],
    "finance": ["finance_knowledge"],
    "general": ["general_knowledge", "conversation_knowledge"],
}


class KnowledgeRouter:
    def route(
        self,
        understanding: dict[str, Any],
        *,
        memory_hits: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        domain = str(understanding.get("domain") or "general")
        sources = list(DOMAIN_SOURCES.get(domain, DOMAIN_SOURCES["general"]))
        # Always allow general fallback source
        if "general_knowledge" not in sources:
            sources.append("general_knowledge")

        packets: list[dict[str, Any]] = []
        # Live tools as knowledge adapters (not domain agents)
        if domain == "time" or understanding.get("intent") == "datetime":
            packets.append(self._date_packet())

        if memory_hits and memory_hits.get("items"):
            packets.append(
                {
                    "source": "memory",
                    "texts": list(memory_hits.get("items") or [])[:6],
                }
            )

        # Fact lookup is a knowledge source, not a category handler
        try:
            from om_ai.knowledge.facts import lookup_fact

            hit = lookup_fact(str(understanding.get("raw") or ""))
            if hit and hit.get("answer"):
                packets.append(
                    {
                        "source": "facts",
                        "texts": [str(hit["answer"])],
                        "meta": hit,
                    }
                )
        except Exception:
            pass

        return {
            "domain": domain,
            "sources": sources,
            "packets": packets,
        }

    def _date_packet(self) -> dict[str, Any]:
        try:
            now = datetime.now(ZoneInfo("Asia/Kolkata"))
        except Exception:
            now = datetime.now().astimezone()
        return {
            "source": "calendar_clock",
            "texts": [
                f"Today's date is {now.strftime('%A, %d %B %Y')}.",
                f"Local time approximately {now.strftime('%H:%M %Z')}.".strip(),
            ],
        }
