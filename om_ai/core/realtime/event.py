from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid

@dataclass
class CompanionEvent:
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    session_id: str = ""
    trace_id: str = ""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "payload": dict(self.payload or {}),
        }
