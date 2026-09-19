from __future__ import annotations
import json, time
from pathlib import Path
from typing import Any

class VisualMemory:
    def __init__(self) -> None:
        self.path = Path("artifacts/companion/visual_memory.jsonl")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, summary: str) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "summary": summary[:500]}) + "\n")
