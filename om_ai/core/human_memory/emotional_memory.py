from __future__ import annotations
import json, time
from pathlib import Path
from typing import Any

class EmotionalMemory:
    def __init__(self) -> None:
        self.path = Path("artifacts/companion/human_memory/emotional.jsonl")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, label: str, *, text: str = "") -> None:
        row = {"ts": time.time(), "label": label, "text": (text or "")[:400]}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def recent(self, limit: int = 10) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        out = []
        for ln in self.path.read_text(encoding="utf-8").splitlines()[-limit:]:
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
        return out
