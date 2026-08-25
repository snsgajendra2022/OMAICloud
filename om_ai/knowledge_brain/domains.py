"""Knowledge domains for OM Universal Knowledge Brain."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeDomain:
    id: str
    name: str
    folder: str
    topics: tuple[str, ...]
    purpose: str


DOMAINS: tuple[KnowledgeDomain, ...] = (
    KnowledgeDomain(
        "history",
        "History Intelligence",
        "history",
        (
            "scientific revolution",
            "enlightenment",
            "industrial revolution",
            "modern science",
            "computing history",
            "AI history 1950–2026",
        ),
        "Connect eras of human progress to present engineering.",
    ),
    KnowledgeDomain(
        "mathematics",
        "Mathematics Brain",
        "mathematics",
        (
            "arithmetic",
            "algebra",
            "geometry",
            "calculus",
            "linear algebra",
            "probability",
            "statistics",
            "optimization",
            "differential equations",
            "information theory",
        ),
        "Foundation for physics, AI, and engineering.",
    ),
    KnowledgeDomain(
        "physics",
        "Physics Brain",
        "physics",
        (
            "classical mechanics",
            "electromagnetism",
            "thermodynamics",
            "quantum mechanics",
            "relativity",
            "materials physics",
            "particle physics",
        ),
        "Physical laws that ground engineering and computing.",
    ),
    KnowledgeDomain(
        "chemistry",
        "Chemistry Brain",
        "chemistry",
        (
            "atoms and molecules",
            "reactions",
            "materials",
            "nanotechnology",
            "energy storage",
            "semiconductor materials",
        ),
        "Materials and energy systems literacy.",
    ),
    KnowledgeDomain(
        "biology",
        "Biology Brain",
        "biology",
        (
            "cell biology",
            "genetics",
            "microbiology",
            "neuroscience",
            "biotechnology",
            "synthetic biology",
            "bio-inspired computing",
        ),
        "Life sciences and bio-inspired systems (research-honest).",
    ),
    KnowledgeDomain(
        "medicine",
        "Medicine Concepts",
        "medicine",
        (
            "human body systems overview",
            "diagnostics concepts",
            "public health",
            "biomedical engineering interfaces",
        ),
        "Conceptual literacy only — not clinical advice.",
    ),
    KnowledgeDomain(
        "engineering",
        "Engineering Brain",
        "engineering",
        (
            "mechanical systems",
            "manufacturing",
            "electrical power",
            "embedded systems",
            "computer engineering",
            "system design",
        ),
        "Build and reason about real-world systems.",
    ),
    KnowledgeDomain(
        "electronics",
        "Electronics Intelligence",
        "electronics",
        (
            "circuits",
            "sensors",
            "microcontrollers",
            "ESP32/Arduino/STM32/RPi",
            "MQTT/Serial/Bluetooth",
            "PCB basics",
        ),
        "Hardware interface literacy for OM embodiment.",
    ),
    KnowledgeDomain(
        "robotics",
        "Robotics Intelligence",
        "robotics",
        (
            "perception",
            "navigation",
            "control",
            "simulation",
            "actuators",
            "safety gates",
        ),
        "Robotics with dry-run defaults and safety.",
    ),
    KnowledgeDomain(
        "programming",
        "Programming Intelligence",
        "programming",
        (
            "Python",
            "JavaScript/TypeScript",
            "Java",
            "C/C++",
            "Rust/Go",
            "SQL",
            "React/FastAPI",
            "testing/devops",
        ),
        "Software engineering practice for OM coding agent.",
    ),
    KnowledgeDomain(
        "computer_science",
        "Computer Science Intelligence",
        "computer_science",
        (
            "algorithms",
            "data structures",
            "OS",
            "networks",
            "databases",
            "distributed systems",
            "security",
        ),
        "CS foundations for scalable systems.",
    ),
    KnowledgeDomain(
        "artificial_intelligence",
        "AI Research Brain",
        "artificial_intelligence",
        (
            "ML",
            "deep learning",
            "transformers",
            "LLMs",
            "SFT/DPO/RLHF",
            "RAG",
            "agents",
            "multimodal",
            "AI safety",
        ),
        "How modern AI systems are built and evaluated.",
    ),
    KnowledgeDomain(
        "business",
        "Business Intelligence",
        "business",
        (
            "finance basics",
            "operations",
            "ERP/CRM",
            "analytics",
            "strategy",
            "product",
        ),
        "Organizational decision support.",
    ),
    KnowledgeDomain(
        "psychology",
        "Human Understanding",
        "psychology",
        (
            "communication",
            "learning",
            "decision making",
            "creativity",
            "UX empathy",
        ),
        "Human factors for better OM responses.",
    ),
    KnowledgeDomain(
        "philosophy",
        "Philosophy & Logic",
        "philosophy",
        (
            "scientific reasoning",
            "ethics",
            "epistemology",
            "logic systems",
        ),
        "Honest reasoning and limits of knowledge.",
    ),
    KnowledgeDomain(
        "future_technology",
        "Future Technology Brain",
        "future_technology",
        (
            "quantum computing",
            "fusion energy",
            "space tech",
            "BCI",
            "neuromorphic",
            "bio computing",
            "advanced robotics",
        ),
        "Label as research/near-future — never claim shipped if not.",
    ),
)


def domains_catalog() -> list[dict]:
    return [
        {
            "id": d.id,
            "name": d.name,
            "folder": d.folder,
            "topics": list(d.topics),
            "purpose": d.purpose,
        }
        for d in DOMAINS
    ]
