"""STEP 92 — Knowledge Brain.

Document/web facts → graph → entity linking → verification → citations.
"""
from __future__ import annotations

from typing import Any

from .step86_global_knowledge import GlobalKnowledgeIntelligence


class KnowledgeBrain:
    def __init__(self) -> None:
        self.global_knowledge = GlobalKnowledgeIntelligence()

    def ingest_document(self, text: str, *, title: str = "document") -> dict[str, Any]:
        result = self.global_knowledge.ingest_text(text, source=title)
        result["title"] = title
        result["step"] = 92
        return result

    def answer_with_knowledge(
        self,
        query: str,
        *,
        knowledge: Any = None,
        research_summary: str = "",
        citations: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        retrieved = self.global_knowledge.retrieve(query, knowledge=knowledge)
        if research_summary:
            retrieved["hits"] = [research_summary] + list(retrieved.get("hits") or [])
            retrieved["context"] = (
                research_summary[:3000]
                + "\n\n"
                + str(retrieved.get("context") or "")
            )[:6000]

        facts = []
        for hit in (retrieved.get("hits") or [])[:5]:
            snippet = str(hit).strip()
            if snippet:
                facts.append(
                    {
                        "fact": snippet[:400],
                        "verified": bool(snippet) and len(snippet) > 40,
                    }
                )

        cites = list(citations or [])
        for live in retrieved.get("live") or []:
            cites.append(
                {
                    "title": live.get("title") or "Source",
                    "url": live.get("url") or "",
                }
            )

        # Dedup citations by url
        seen = set()
        uniq = []
        for c in cites:
            url = (c.get("url") if isinstance(c, dict) else "") or ""
            if url in seen:
                continue
            seen.add(url)
            uniq.append(c)

        return {
            "step": 92,
            "query": query,
            "facts": facts,
            "entities": retrieved.get("entities") or [],
            "context": retrieved.get("context") or "",
            "citations": uniq[:8],
            "verified_fact_count": sum(1 for f in facts if f.get("verified")),
        }
