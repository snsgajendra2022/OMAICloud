"""
STEP 88 — OM Advanced Knowledge Brain

Information → Understanding → Knowledge Graph → Memory → Reasoning
"""
from __future__ import annotations

from typing import Any


class AdvancedKnowledgeBrain:
    """World-knowledge facade: graph + RAG + vector + entity linking."""

    def ingest(self, text: str, *, source: str = "chat") -> dict[str, Any]:
        """Understand text and grow the knowledge graph."""
        data = self._entities_from_text(text)
        graph: dict[str, Any] = {}
        try:
            from om_ai.knowledge.graph.engine import KnowledgeGraphEngine

            graph = KnowledgeGraphEngine().process(data, source) or {}
        except Exception as exc:
            graph = {"error": str(exc)}

        # Persist salient facts into semantic memory
        try:
            from om_ai.memory.memory_manager import AdvancedMemorySystem

            mem = AdvancedMemorySystem()
            if data:
                mem.remember_fact(
                    f"[{source}] " + ", ".join(f"{k}={v}" for k, v in list(data.items())[:8]),
                    importance=0.7,
                )
        except Exception:
            pass

        return {
            "entities": data,
            "graph": graph,
            "source": source,
        }

    def retrieve(self, query: str, *, k: int = 6) -> dict[str, Any]:
        """RAG + vector + graph-aware retrieval."""
        hits: list[dict[str, Any]] = []
        try:
            from om_ai.knowledge.retrieval import search_knowledge

            for h in search_knowledge(query, k=k) or []:
                if isinstance(h, dict):
                    hits.append(h)
                else:
                    hits.append({"content": str(h)})
        except Exception:
            try:
                from om_ai.agent.tools import search_knowledge as sk

                for s in sk(query, k=k) or []:
                    hits.append(s if isinstance(s, dict) else {"content": str(s)})
            except Exception:
                pass

        # Memory layer
        memory_bits: list[str] = []
        try:
            from om_ai.memory.memory_manager import AdvancedMemorySystem

            pack = AdvancedMemorySystem().recall(query, k=4)
            memory_bits = list(pack.get("snippets") or [])[:4]
        except Exception:
            pass

        # Entity linking hint
        entities = self._entities_from_text(query)

        text_parts = []
        for h in hits[:k]:
            c = str(h.get("content") or h.get("answer") or h.get("text") or "").strip()
            if c:
                text_parts.append(c[:500])
        text_parts.extend(memory_bits)

        verified = self.verify_facts(text_parts[:3])

        return {
            "query": query,
            "hits": hits[:k],
            "entities": entities,
            "memory": memory_bits,
            "verified": verified,
            "text": "\n\n".join(text_parts)[:4000],
            "ok": bool(text_parts),
        }

    def understand_and_store(self, information: str, *, source: str = "ingest") -> dict[str, Any]:
        """Full flow: Information → Understanding → Graph → Memory."""
        ingested = self.ingest(information, source=source)
        retrieved = self.retrieve(information, k=4)
        return {
            "ingest": ingested,
            "retrieve": retrieved,
            "flow": [
                "information",
                "understanding",
                "knowledge_graph",
                "memory",
                "reasoning_ready",
            ],
        }

    def verify_facts(self, claims: list[str]) -> dict[str, Any]:
        """Lightweight fact verification — cross-check against knowledge hits."""
        results: list[dict[str, Any]] = []
        for claim in claims[:5]:
            c = (claim or "").strip()
            if len(c) < 12:
                continue
            support = 0
            try:
                from om_ai.knowledge.retrieval import search_knowledge

                hits = search_knowledge(c[:120], k=2) or []
                support = len(hits)
            except Exception:
                support = 0
            results.append(
                {
                    "claim": c[:200],
                    "supported": support > 0,
                    "support_hits": support,
                }
            )
        return {
            "checked": len(results),
            "supported": sum(1 for r in results if r["supported"]),
            "results": results,
        }

    def update_knowledge(self, key: str, value: str, *, source: str = "update") -> dict[str, Any]:
        return self.ingest(f"{key}: {value}", source=source)

    def _entities_from_text(self, text: str) -> dict[str, str]:
        data: dict[str, str] = {}
        known = {
            "python",
            "react",
            "laravel",
            "php",
            "composer",
            "fastapi",
            "django",
            "ai",
            "india",
            "sqlite",
            "docker",
            "kubernetes",
        }
        for tok in (text or "").replace(",", " ").split():
            clean = tok.strip(".,;:()[]{}\"'").strip()
            if not clean:
                continue
            low = clean.lower()
            if low in known:
                data[low] = clean
            elif len(clean) >= 3 and clean[0].isupper() and clean.isalpha():
                data[low] = clean
        return data
