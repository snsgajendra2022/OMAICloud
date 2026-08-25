"""Combined catalog for OM Knowledge Brain."""
from __future__ import annotations

from typing import Any

from .directive import KNOWLEDGE_SYSTEM
from .domains import domains_catalog
from .eras import eras_catalog


def knowledge_catalog() -> dict[str, Any]:
    return {
        "name": "om-knowledge-brain-v1",
        "coverage": "1600–2026",
        "system": KNOWLEDGE_SYSTEM,
        "eras": eras_catalog(),
        "domains": domains_catalog(),
        "stack": {
            "models": ["OM-1.0", "OM-7.0", "OM-70.0"],
            "layers": [
                "Experience Layer",
                "Cognitive Operating System",
                "Intelligence Core",
                "Memory",
                "Knowledge",
                "Agents",
                "Tools",
                "Multimodal",
                "Hardware/Robotics (gated)",
                "Research (honest horizons)",
            ],
            "implementation_path": [
                "Corpus folders + licensed docs",
                "RAG / vector retrieval",
                "Instruction SFT (this package)",
                "Preference training",
                "Scale model size with compute",
            ],
        },
        "honesty": (
            "This catalog organizes a knowledge ecosystem. It does not claim that "
            "all human knowledge from 1600–2026 is already inside OM weights."
        ),
    }
