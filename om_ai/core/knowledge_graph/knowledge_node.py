from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class KnowledgeNode:
    """
    Represents a concept inside OM Knowledge Graph.
    """

    id: str

    name: str

    domain: str

    description: str = ""

    difficulty: float = 0.0

    skills: list[str] = field(
        default_factory=list
    )

    prerequisites: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


    def to_dict(self):

        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain,
            "description": self.description,
            "difficulty": self.difficulty,
            "skills": self.skills,
            "prerequisites": self.prerequisites,
            "metadata": self.metadata,
        }