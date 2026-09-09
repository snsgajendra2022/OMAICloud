from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MemoryItem:


    content: str


    memory_type: str = "general"


    importance: float = 0.0


    tags: list[str] = field(
        default_factory=list
    )


    metadata: dict[str, Any] = field(
        default_factory=dict
    )


    created_at: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )