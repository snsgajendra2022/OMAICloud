from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import uuid

@dataclass
class RuntimeContext:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default"
    project_id: str = "default"
    meta: dict[str, Any] = field(default_factory=dict)
