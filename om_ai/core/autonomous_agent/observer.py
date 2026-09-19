from __future__ import annotations
from typing import Any

class Observer:
    def note(self, event: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
        return {"event": event, "detail": detail or {}}
