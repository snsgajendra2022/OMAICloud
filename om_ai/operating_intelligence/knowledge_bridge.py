"""Knowledge bridge — RAG + dataset brain + optional live knowledge."""
from __future__ import annotations

from typing import Any


def research(query: str, *, tenant_id: str = "default", k: int = 6) -> dict[str, Any]:
    snippets: list[str] = []
    source = "none"
    grounded = ""

    try:
        from om_ai.brain.dataset_engine import retrieve_answer

        hit = retrieve_answer(query)
        if hit and hit.get("answer"):
            grounded = str(hit["answer"])
            snippets.append(grounded[:900])
            source = "dataset_brain"
    except Exception:
        pass

    try:
        from om_ai.agent.tools import search_knowledge

        for s in search_knowledge(query, tenant_id=tenant_id, k=k) or []:
            if s and s not in snippets:
                snippets.append(s[:400])
        if source == "none" and snippets:
            source = "rag"
    except Exception:
        pass

    try:
        from om_ai.knowledge.selector import select_knowledge

        profile = select_knowledge(query, snippets)
        snippets = profile.kept or snippets
        extra = {
            "important": profile.important,
            "not_important": profile.not_important,
            "dropped": profile.dropped,
            "topic": profile.topic,
        }
    except Exception:
        extra = {}

    try:
        from om_ai.knowledge.ranker import detect_domain, rank_sources

        ranked = rank_sources(query, snippets)
        extra["domain"] = ranked.domain or detect_domain(query)
        extra["ranked"] = ranked.to_dict()
        if ranked.ranked:
            snippets = [r.text for r in ranked.ranked]
        extra["dropped"] = list(extra.get("dropped") or []) + ranked.dropped
    except Exception:
        extra.setdefault("domain", "general")

    return {
        "snippets": snippets[:k],
        "grounded_reply": grounded,
        "source": source,
        "count": len(snippets),
        **extra,
    }
