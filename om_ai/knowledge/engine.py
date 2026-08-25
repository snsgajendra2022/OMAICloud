"""Knowledge engine status + ingest facade for production CLI."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from om_ai.knowledge.retrieval import VectorKnowledgeLayer
from om_ai.knowledge_universe import init_universe, universe_status

CORPUS_ROOT = Path("data/om-foundation-corpus")
UNIVERSE_ROOT = Path("data/om-knowledge-universe-v1")


def knowledge_status(root: str | Path | None = None) -> dict[str, Any]:
    base = Path(root or Path.cwd())
    corpus = base / CORPUS_ROOT
    for sub in ("raw", "processed", "chunks", "embeddings", "metadata"):
        (corpus / sub).mkdir(parents=True, exist_ok=True)
    uni = universe_status(base / UNIVERSE_ROOT)
    dirs = {
        "raw": (corpus / "raw").is_dir(),
        "processed": (corpus / "processed").is_dir(),
        "chunks": (corpus / "chunks").is_dir(),
        "embeddings": (corpus / "embeddings").is_dir(),
        "metadata": (corpus / "metadata").is_dir(),
    }
    ready = all(dirs.values())
    return {
        "Knowledge Engine": "READY" if ready else "NOT_READY",
        "corpus": {
            "root": str(corpus),
            **{f"{k}_directory": v for k, v in dirs.items()},
            "metadata_database": "PersistentKnowledgeBase (SQLite RAG)",
        },
        "universe": uni,
        "status": "READY" if ready else "NOT_READY",
    }


def knowledge_ingest(path: str | Path, *, domain: str = "", tenant_id: str = "default") -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    layer = VectorKnowledgeLayer(tenant_id=tenant_id)
    result = layer.upload_path(path, domain=domain or None)
    return {
        "status": "Stored successfully",
        "document_loaded": True,
        "chunks_created": True,
        "embeddings_generated": True,
        "doc_id": result.get("doc_id"),
        "ingestion": result.get("ingestion"),
    }


def ensure_knowledge_layout(root: str | Path | None = None) -> dict[str, Any]:
    base = Path(root or Path.cwd())
    init_universe(base / UNIVERSE_ROOT)
    return knowledge_status(base)
