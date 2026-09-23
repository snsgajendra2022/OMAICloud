"""Document loader adapter."""
from __future__ import annotations

from typing import Any


class DocumentLoader:
    def load(self, path: str) -> dict[str, Any]:
        try:
            from pathlib import Path

            p = Path(path)
            text = p.read_text(encoding="utf-8", errors="ignore")[:50000]
            return {"ok": True, "path": str(p), "text": text, "chars": len(text)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


document_loader = DocumentLoader
