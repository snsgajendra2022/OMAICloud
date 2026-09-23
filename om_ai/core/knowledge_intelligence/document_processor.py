"""Document processor — clean text chunks for embedding."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class DocumentProcessor:
    def process(self, path: Path | str) -> dict[str, Any]:
        p = Path(path)
        raw = p.read_text(encoding="utf-8", errors="ignore")
        text = re.sub(r"\s+", " ", raw).strip()
        chunks = []
        step = 800
        for i in range(0, len(text), step):
            chunk = text[i : i + step].strip()
            if chunk:
                chunks.append(chunk)
        return {
            "path": str(p),
            "title": p.name,
            "text": text[:50000],
            "chunks": chunks[:200],
            "source": "document",
        }
