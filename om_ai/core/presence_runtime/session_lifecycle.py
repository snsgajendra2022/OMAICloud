"""Session lifecycle for presence runtime."""
from __future__ import annotations

import time
import uuid
from typing import Any


class SessionLifecycle:
    def __init__(self) -> None:
        self.session_id = str(uuid.uuid4())
        self.started_ms = time.time() * 1000
        self.turn_count = 0
        self.last_user_ms = 0.0
        self.last_assistant_ms = 0.0

    def on_user(self) -> None:
        self.turn_count += 1
        self.last_user_ms = time.time() * 1000

    def on_assistant(self) -> None:
        self.last_assistant_ms = time.time() * 1000

    def snapshot(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_ms": self.started_ms,
            "turn_count": self.turn_count,
            "uptime_ms": time.time() * 1000 - self.started_ms,
            "last_user_ms": self.last_user_ms,
            "last_assistant_ms": self.last_assistant_ms,
        }
