"""OM live knowledge — retrieval infrastructure, not an LLM."""

from om_ai.live_knowledge.engine import LiveKnowledgeEngine, live_knowledge_enabled, network_enabled
from om_ai.live_knowledge.freshness import (
    FreshnessRouter,
    is_chitchat,
    is_greeting_like,
    is_om_self_query,
    needs_live_knowledge,
)
from om_ai.live_knowledge.router import enrich_messages_for_live_knowledge

__all__ = [
    "FreshnessRouter",
    "LiveKnowledgeEngine",
    "is_chitchat",
    "is_greeting_like",
    "is_om_self_query",
    "needs_live_knowledge",
    "enrich_messages_for_live_knowledge",
    "live_knowledge_enabled",
    "network_enabled",
]
