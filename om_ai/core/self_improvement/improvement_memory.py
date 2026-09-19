from __future__ import annotations
import json, time
from pathlib import Path
from typing import Any

class ImprovementMemory:
    def __init__(self) -> None:
        self.path = Path("artifacts/companion/self_improvement.jsonl")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: dict[str, Any]) -> None:
        row = {"ts": time.time(), **event}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
