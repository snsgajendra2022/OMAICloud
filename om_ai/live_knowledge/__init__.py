"""OM live knowledge — retrieval infrastructure, not an LLM."""

from om_ai.live_knowledge.freshness import FreshnessRouter, needs_live_knowledge
from om_ai.live_knowledge.router import enrich_messages_for_live_knowledge

__all__ = [
    "FreshnessRouter",
    "needs_live_knowledge",
    "enrich_messages_for_live_knowledge",
]
