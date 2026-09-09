from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class KnowledgeItem:


    title: str

    content: str

    category: str = "general"

    source: str = ""

    confidence: float = 0.0

    tags: list[str] = field(
        default_factory=list
    )

    created_at: str = field(
        default_factory=lambda:
        datetime.utcnow().isoformat()
    )