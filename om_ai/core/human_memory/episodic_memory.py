from __future__ import annotations
import json, time, uuid
from pathlib import Path
from typing import Any

class EpisodicMemory:
    def __init__(self, path: Path | None = None) -> None:
        root = Path("artifacts/companion/human_memory")
        root.mkdir(parents=True, exist_ok=True)
        self.path = path or (root / "episodic.jsonl")

    def add(self, text: str, *, role: str = "user", tags: list[str] | None = None) -> dict[str, Any]:
        row = {
            "id": uuid.uuid4().hex[:12],
            "ts": time.time(),
            "role": role,
            "text": (text or "")[:2000],
            "tags": tags or [],
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-limit:]
        out = []
        for ln in lines:
            try:
                out.append(json.loads(ln))
            except Exception:
                pass
        return out
