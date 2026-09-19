"""Short-term turn buffer (current conversation window)."""
from __future__ import annotations

from collections import deque
from typing import Any


class ShortTermMemory:
    def __init__(self, limit: int = 24) -> None:
        self._buf: deque[dict[str, Any]] = deque(maxlen=limit)

    def add(self, role: str, content: str) -> None:
        c = (content or "").strip()
        if not c:
            return
        self._buf.append({"role": role, "content": c[:2000]})

    def history(self, limit: int = 14) -> list[dict[str, Any]]:
        return list(self._buf)[-limit:]

    def clear(self) -> None:
        self._buf.clear()
