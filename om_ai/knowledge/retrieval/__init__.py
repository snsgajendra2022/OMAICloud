"""Vector knowledge layer — wraps PersistentKnowledgeBase + local corpus index."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from om_ai.knowledge.ingestion import ingest_file
from om_ai.knowledge.rag import PersistentKnowledgeBase


class VectorKnowledgeLayer:
    """Search + ingest into OM persistent RAG (hashed TF-IDF embeddings)."""

    def __init__(self, *, tenant_id: str = "default", corpus_root: str | Path | None = None) -> None:
        self.tenant_id = tenant_id
        self.kb = PersistentKnowledgeBase()
        self.corpus_root = Path(corpus_root or "data/om-knowledge-universe-v1/knowledge")

    def upload_path(self, path: str | Path, *, domain: str | None = None) -> dict[str, Any]:
        path = Path(path)
        run_root = Path("data/om-foundation-corpus")
        info = ingest_file(path, out_root=run_root)
        meta = dict(info["metadata"])
        if domain:
            meta["domain"] = domain
        doc_id = self.kb.ingest_file(path, self.tenant_id, metadata=meta)
        return {"doc_id": doc_id, "ingestion": info}

    def search(self, query: str, *, k: int = 5) -> list[dict[str, Any]]:
        hits = self.kb.search(query, self.tenant_id, k=k)
        out: list[dict[str, Any]] = []
        for h in hits or []:
            if hasattr(h, "text"):
                out.append(
                    {
                        "text": str(h.text)[:500],
                        "score": float(getattr(h, "score", 0.0) or 0.0),
                        "doc_id": getattr(h, "doc_id", ""),
                        "metadata": getattr(h, "metadata", {}) or {},
                    }
                )
            elif isinstance(h, dict):
                out.append(h)
        return out


def search_knowledge(query: str, *, tenant_id: str = "default", k: int = 5) -> list[dict[str, Any]]:
    return VectorKnowledgeLayer(tenant_id=tenant_id).search(query, k=k)


def upload_document(path: str, *, tenant_id: str = "default", domain: str | None = None) -> dict[str, Any]:
    return VectorKnowledgeLayer(tenant_id=tenant_id).upload_path(path, domain=domain)
