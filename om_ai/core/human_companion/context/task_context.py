"""Task context — what work is in flight."""
from __future__ import annotations

import re
from typing import Any


class TaskContext:
    def __init__(self) -> None:
        self.active: str = ""

    def infer(
        self,
        message: str,
        *,
        history: list[dict[str, Any]] | None = None,
        topic: str = "general",
    ) -> dict[str, Any]:
        low = (text := (message or "")).lower()
        if re.search(r"\b(continue|keep going|us[ei]|wahi)\b", low) and self.active:
            summary = self.active
        elif topic and topic != "general":
            summary = f"Working on {topic.replace('_', ' ')}"
            self.active = summary
        else:
            summary = self.active or (text[:80] if text else "")
            if text and len(text.split()) > 3:
                self.active = text[:120]
                summary = self.active
        return {"summary": summary, "topic": topic, "active": self.active}
