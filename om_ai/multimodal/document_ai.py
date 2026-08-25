"""Document AI — text/PDF/docx understanding without vision weights."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def analyze_document(path: str | Path, *, question: str = "") -> dict[str, Any]:
    """Extract text, chunk summary, optional reasoning over the doc."""
    path = Path(path)
    if not path.is_file():
        return {"ok": False, "error": f"missing file: {path}", "modality": "document"}
    from om_ai.knowledge.ingestion import load_text, clean_text, chunk_text, build_metadata

    raw = load_text(path)
    text = clean_text(raw)
    meta = build_metadata(path, text)
    chunks = chunk_text(text, size=600, overlap=80)
    preview = text[:1200]
    answer = ""
    if question.strip():
        from om_ai.core.reasoning.pipeline import run_reasoning_pipeline

        hits = [c[:400] for c in chunks[:4]]
        result = run_reasoning_pipeline(
            f"{question.strip()}\n\nDocument: {path.name}",
            knowledge_hits=hits,
            retrieve=False,
        )
        answer = result.get("markdown") or result.get("solution") or ""
    return {
        "ok": True,
        "modality": "document",
        "path": str(path),
        "metadata": meta.to_dict() if hasattr(meta, "to_dict") else dict(meta.__dict__),
        "chars": len(text),
        "chunks": len(chunks),
        "preview": preview,
        "answer": answer,
        "note": "Document AI uses text extraction + reasoning (no vision weights required).",
    }


def multimodal_status() -> dict[str, Any]:
    return {
        "document": "ready",
        "vision": "stub — needs trained vision weights",
        "voice": "stub — needs ASR/TTS weights",
        "image": "stub — describe_image unavailable until vision wired",
        "video": "not implemented",
        "how_to": {
            "document": "from om_ai.multimodal.document_ai import analyze_document",
            "orchestrator": "UnifiedOrchestrator(...).run(documents=[...])",
        },
    }
