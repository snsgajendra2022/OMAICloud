"""Knowledge Factory — ingest → classify → chunk → embed/index → graph."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def process_document(path: str | Path, *, tenant_id: str = "default") -> dict[str, Any]:
    path = Path(path)
    from om_ai.knowledge.corpus import ensure_corpus_layout
    from om_ai.knowledge.graph import KnowledgeGraph
    from om_ai.knowledge.ingestion import build_metadata, chunk_text, clean_text, load_text
    from om_ai.knowledge.retrieval import VectorKnowledgeLayer

    ensure_corpus_layout()
    raw = load_text(path)
    text = clean_text(raw)
    meta = build_metadata(path, text)
    chunks = chunk_text(text)
    layer = VectorKnowledgeLayer(tenant_id=tenant_id)
    up = layer.upload_path(path, domain=meta.domain)
    graph = KnowledgeGraph("artifacts/system/knowledge_graph.json")
    graph.add_triple(meta.title or path.stem, "in_domain", meta.domain)
    for topic in (meta.topics or [])[:5]:
        graph.add_triple(meta.title or path.stem, "about", topic)
    graph.save()
    report = {
        "ok": True,
        "path": str(path),
        "doc_id": up.get("doc_id"),
        "domain": meta.domain,
        "topics": meta.topics,
        "chunks": len(chunks),
        "chars": len(text),
        "graph_nodes": graph.node_count(),
        "ts": time.time(),
    }
    out = Path("artifacts/knowledge_factory")
    out.mkdir(parents=True, exist_ok=True)
    (out / "latest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def process_directory(root: str | Path, *, limit: int = 20) -> dict[str, Any]:
    root = Path(root)
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".txt", ".md", ".json", ".csv"}]
    results = []
    for p in files[:limit]:
        try:
            results.append(process_document(p))
        except Exception as exc:
            results.append({"ok": False, "path": str(p), "error": str(exc)})
    return {"processed": len(results), "ok": sum(1 for r in results if r.get("ok")), "results": results}
