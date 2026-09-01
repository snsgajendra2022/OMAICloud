"""Knowledge bridge — RAG + dataset brain + fact table + vector index."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def research(query: str, *, tenant_id: str = "default", k: int = 6) -> dict[str, Any]:
    snippets: list[str] = []
    source = "none"
    grounded = ""
    extra: dict[str, Any] = {}

    try:
        from om_ai.knowledge.facts import lookup_fact

        fact = lookup_fact(query)
        if fact and fact.get("answer"):
            grounded = str(fact["answer"])
            snippets.append(grounded[:900])
            source = "fact_table"
            extra["entities"] = fact.get("entities") or {}
            extra["fact_id"] = fact.get("id")
            try:
                from om_ai.knowledge.embeddings import EmbeddingIndex

                EmbeddingIndex().upsert(
                    grounded,
                    tenant_id=tenant_id,
                    metadata={"domain": fact.get("domain") or "civics", "id": fact.get("id")},
                    doc_id=str(fact.get("id") or "fact"),
                )
            except Exception as exc:
                logger.debug("fact embed upsert skipped: %s", exc)
    except Exception as exc:
        logger.debug("fact lookup skipped: %s", exc)

    try:
        from om_ai.brain.dataset_engine import retrieve_answer

        hit = retrieve_answer(query)
        if hit and hit.get("answer"):
            ans = str(hit["answer"])
            if not grounded:
                grounded = ans
            if ans not in snippets:
                snippets.append(ans[:900])
            if source == "none":
                source = "dataset_brain"
    except Exception:
        pass

    try:
        from om_ai.knowledge.retrieval import VectorKnowledgeLayer

        for row in VectorKnowledgeLayer(tenant_id=tenant_id).search(query, k=k) or []:
            text = str(row.get("text") or "")
            if text and text not in snippets:
                snippets.append(text[:400])
        if source == "none" and snippets:
            source = "vector"
    except Exception:
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
        extra.update(
            {
                "important": profile.important,
                "not_important": profile.not_important,
                "dropped": profile.dropped,
                "topic": profile.topic,
            }
        )
    except Exception:
        extra.setdefault("dropped", [])

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
