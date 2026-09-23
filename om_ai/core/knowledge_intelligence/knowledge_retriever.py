"""Knowledge retriever — relevant chunks only into LLM context."""
from __future__ import annotations

from typing import Any

from .vector_memory import VectorMemory


class KnowledgeRetriever:
    def retrieve(self, query: str, *, limit: int = 5) -> dict[str, Any]:
        hits = VectorMemory().search(query, limit=limit)
        blob = "\n".join(f"- {h.get('text', '')[:300]}" for h in hits if h.get("text"))
        return {
            "hits": hits,
            "context": blob[:3000],
            "policy": "vector_retrieval_not_prompt_dump",
        }
