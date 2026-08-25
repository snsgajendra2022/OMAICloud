"""Data processing stage — clean/chunk before embeddings."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def process_raw_file(path: str | Path) -> dict[str, Any]:
    from om_ai.knowledge.ingestion import build_metadata, chunk_text, clean_text, load_text

    path = Path(path)
    text = clean_text(load_text(path))
    meta = build_metadata(path, text)
    chunks = chunk_text(text)
    out_dir = Path("data_platform/processing/out")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{meta.doc_id}.txt"
    out.write_text(text, encoding="utf-8")
    return {
        "ok": True,
        "doc_id": meta.doc_id,
        "domain": meta.domain,
        "chunks": len(chunks),
        "output": str(out),
    }
