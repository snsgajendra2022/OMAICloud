"""Knowledge updater — append approved learnings to local growth store."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class KnowledgeUpdater:
    def upsert(self, doc: dict[str, Any]) -> dict[str, Any]:
        try:
            root = Path("artifacts") / "companion" / "knowledge_growth"
            root.mkdir(parents=True, exist_ok=True)
            path = root / "approved_sources.jsonl"
            row = {
                "ts": time.time(),
                "title": str(doc.get("title") or "")[:200],
                "source": str(doc.get("source") or "approved")[:120],
                "text": str(doc.get("text") or "")[:2000],
                "chunks": len(doc.get("chunks") or []),
            }
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            return {"ok": True, "stored": True, "path": str(path)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
