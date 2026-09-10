"""STEP 86 — Global Knowledge Intelligence.

Local knowledge + live retrieval + graph facts + ranking.
"""
from __future__ import annotations

from typing import Any


class GlobalKnowledgeIntelligence:
    def __init__(self) -> None:
        self._graph: dict[str, list[str]] = {}

    def ingest_text(self, text: str, *, source: str = "local") -> dict[str, Any]:
        words = [w.lower() for w in (text or "").split() if len(w) > 3][:40]
        entities = list(dict.fromkeys(words))[:12]
        for e in entities:
            self._graph.setdefault(e, [])
            for other in entities:
                if other != e and other not in self._graph[e]:
                    self._graph[e].append(other)
        return {"step": 86, "ingested": True, "entities": entities, "source": source}

    def link_entities(self, query: str) -> list[dict[str, Any]]:
        q_words = set((query or "").lower().split())
        linked = []
        for entity, neighbors in self._graph.items():
            if entity in q_words or any(w in entity for w in q_words):
                linked.append({"entity": entity, "links": neighbors[:8]})
        return linked[:10]

    def retrieve(self, query: str, knowledge: Any = None) -> dict[str, Any]:
        hits: list[str] = []
        if isinstance(knowledge, list):
            hits.extend(str(x)[:1500] for x in knowledge[:8] if x)
        elif isinstance(knowledge, dict):
            for k in ("hits", "results", "documents", "context"):
                v = knowledge.get(k)
                if isinstance(v, list):
                    hits.extend(str(x)[:1500] for x in v[:8])
                elif isinstance(v, str) and v.strip():
                    hits.append(v[:1500])
        elif isinstance(knowledge, str) and knowledge.strip():
            hits.append(knowledge[:2000])

        # Live knowledge when query looks global/current
        live = []
        q = (query or "").lower()
        if any(w in q for w in ("latest", "current", "world", "global", "what is", "who is")):
            try:
                from om_ai.live_knowledge.web_search import search_web

                for h in search_web(query, limit=4) or []:
                    live.append(
                        {
                            "title": getattr(h, "title", ""),
                            "url": getattr(h, "url", ""),
                            "snippet": getattr(h, "snippet", ""),
                        }
                    )
                    if getattr(h, "snippet", None):
                        hits.append(str(h.snippet)[:800])
            except Exception:
                pass

        for h in hits[:5]:
            self.ingest_text(h, source="retrieved")

        return {
            "step": 86,
            "query": query,
            "hits": hits[:10],
            "live": live,
            "entities": self.link_entities(query),
            "context": "\n\n".join(hits[:6])[:6000],
        }
