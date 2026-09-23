"""Knowledge ingestion — approved sources into the knowledge base (not prompt stuffing)."""
from __future__ import annotations

from pathlib import Path
from typing import Any


class KnowledgeIngestion:
    def ingest_file(self, path: str) -> dict[str, Any]:
        p = Path(path)
        if not p.is_file():
            return {"ok": False, "error": "missing_file"}
        try:
            from .document_processor import DocumentProcessor
            from .knowledge_updater import KnowledgeUpdater

            doc = DocumentProcessor().process(p)
            return KnowledgeUpdater().upsert(doc)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def ingest_text(self, text: str, *, source: str = "approved") -> dict[str, Any]:
        try:
            from .knowledge_updater import KnowledgeUpdater

            return KnowledgeUpdater().upsert(
                {"text": (text or "")[:20000], "source": source, "title": source}
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
