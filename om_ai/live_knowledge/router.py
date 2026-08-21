"""Wire freshness → real retrieval → context for OM-1.0 (never another LLM)."""
from __future__ import annotations

from typing import Any

from om_ai.live_knowledge.engine import (
    LiveKnowledgeEngine,
    inject_context,
    live_knowledge_enabled,
)
from om_ai.live_knowledge.freshness import FreshnessRouter
from om_ai.live_knowledge.search import LocalSearchIndex


def enrich_messages_for_live_knowledge(
    messages: list[dict],
    *,
    index: LocalSearchIndex | None = None,
    router: FreshnessRouter | None = None,
    allow_network: bool | None = None,
    prefer_grounded_reply: bool | None = None,
    force: bool = False,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """If query looks time-sensitive, attach retrieval context (never another LLM).

    When network retrieval yields usable evidence, ``meta["grounded_reply"]`` holds a
    deterministic answer assembled from sources. Callers may return that directly
    (still not an external LLM) when OM-1.0's context window is too small to synthesize.
    """
    if not live_knowledge_enabled():
        normalized = [
            {"role": str(m.get("role") or "user"), "content": str(m.get("content") or "")}
            for m in messages
        ]
        return normalized, {
            "needs_live": False,
            "reason": "disabled",
            "hits": [],
            "fetches": [],
            "llm_used": None,
        }

    engine = LiveKnowledgeEngine(index=index, router=router, allow_network=allow_network)
    # If caller passed an empty custom index, don't replace with default cache
    if index is not None:
        engine.index = index

    result = engine.collect(messages, force=force)
    meta: dict[str, Any] = dict(result.meta)
    meta["grounded_reply"] = result.grounded_reply
    meta["llm_used"] = None

    if prefer_grounded_reply is None:
        # Never paste web dumps as the chat reply by default — users expect
        # normal assistant text. Retrieval still injects context for OM-1.0;
        # grounded extract is only used when the caller sets prefer=True
        # (e.g. after degenerate native output).
        prefer_grounded_reply = False
    meta["prefer_grounded_reply"] = prefer_grounded_reply

    if not result.needs_live:
        return [
            {"role": str(m.get("role") or "user"), "content": str(m.get("content") or "")}
            for m in messages
        ], meta

    out = inject_context(messages, result.context_block)
    return out, meta
