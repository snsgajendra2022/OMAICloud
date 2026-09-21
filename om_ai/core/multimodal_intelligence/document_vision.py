"""Document / PDF vision hooks."""
from __future__ import annotations

from typing import Any


class DocumentVision:
    def read(self, doc_ref: str | None = None) -> dict[str, Any]:
        if not doc_ref:
            return {"has_document": False, "pages": 0, "text_preview": ""}
        return {
            "has_document": True,
            "doc_ref": doc_ref,
            "pages": 0,
            "text_preview": "",
            "system_hint": "Document attached — extract relevant sections before answering.",
        }
