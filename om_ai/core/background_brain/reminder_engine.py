from __future__ import annotations
import time
from typing import Any

class ReminderEngine:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    def add(self, text: str, *, when_ts: float | None = None) -> dict[str, Any]:
        row = {"text": text, "when_ts": when_ts or (time.time() + 3600), "done": False}
        self.items.append(row)
        return row

    def due(self) -> list[dict[str, Any]]:
        now = time.time()
        return [i for i in self.items if not i.get("done") and float(i.get("when_ts") or 0) <= now]
