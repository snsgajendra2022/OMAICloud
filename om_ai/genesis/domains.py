"""OM-1.0 Genesis-JARVIS — 19-layer intelligence map for training corpora."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Domain:
    id: str
    name: str
    horizon: str  # current | near_future | research
    layer: int  # 1..19 Universal Intelligence stack
    topics: tuple[str, ...]
    example_kinds: tuple[str, ...]  # instruction example families


# Universal Intelligence System layers → trainable domains
DOMAINS: tuple[Domain, ...] = (
    Domain(
        "cognitive_core",
        "Cognitive Core",
        "current",
        1,
        (
            "reasoning",
            "planning",
            "decision making",
            "problem decomposition",
            "prediction",
            "self-evaluation",
            "Observe-Understand-Plan-Execute-Verify-Improve",
        ),
        ("architecture", "reasoning", "checklist"),
    ),
    Domain(
        "human_understanding",
        "Human Understanding",
        "current",
        2,
        (
            "natural language",
            "technical language",
            "business language",
            "scientific language",
            "intent disambiguation",
            "emotion/context cues",
        ),
        ("intent", "clarify", "explain"),
    ),
    Domain(
        "knowledge_engine",
        "Universal Knowledge Engine",
        "current",
        3,
        (
            "knowledge graphs",
            "concept relationships",
            "science/tech/math overview",
            "RAG grounding",
            "citation honesty",
        ),
        ("explain", "compare", "retrieve-plan"),
    ),
    Domain(
        "software",
        "Software Engineering Brain",
        "current",
        4,
        (
            "system design",
            "API design",
            "databases",
            "security",
            "DevOps",
            "testing",
            "Python/FastAPI",
            "TypeScript/React",
            "repo understanding",
        ),
        ("architecture", "coding", "review"),
    ),
    Domain(
        "autonomous_coding",
        "Autonomous Coding Agents",
        "current",
        5,
        (
            "architecture agent",
            "backend/frontend agents",
            "database agent",
            "security/testing/devops agents",
            "requirement→deploy workflow",
        ),
        ("agent-plan", "workflow", "coding"),
    ),
    Domain(
        "memory",
        "Memory Architecture",
        "current",
        6,
        (
            "short-term memory",
            "long-term memory",
            "experience memory",
            "skill memory",
            "memory→knowledge→decisions",
        ),
        ("architecture", "explain", "checklist"),
    ),
    Domain(
        "digital_twin",
        "Digital Twin Intelligence",
        "near_future",
        7,
        (
            "software project twin",
            "device/machine twin",
            "environment twin",
            "simulate-before-change",
            "school transport twin example",
        ),
        ("architecture", "simulation", "scenario"),
    ),
    Domain(
        "agent_civilization",
        "Agent Civilization",
        "current",
        8,
        (
            "OM master agent",
            "research/engineering/science agents",
            "business/security/automation/hardware agents",
            "agent collaboration protocols",
        ),
        ("agent-plan", "workflow", "architecture"),
    ),
    Domain(
        "electronics",
        "Electronics Intelligence",
        "current",
        9,
        (
            "ESP32",
            "Arduino",
            "STM32",
            "Raspberry Pi",
            "Jetson",
            "FPGA basics",
            "MQTT/CAN/BLE/WiFi/Serial",
            "sensors and PCB basics",
        ),
        ("architecture", "electronics", "checklist"),
    ),
    Domain(
        "robotics",
        "Robotics Intelligence",
        "current",
        10,
        (
            "robot controller stack",
            "vision/navigation",
            "motion planning",
            "actuators/motors",
            "safety e-stop",
            "sim-first autonomy",
        ),
        ("architecture", "robotics", "scenario"),
    ),
    Domain(
        "scientific_research",
        "Scientific Research Engine",
        "current",
        11,
        (
            "hypothesis design",
            "experiment planning",
            "physics/chemistry/biology concepts",
            "materials and energy basics",
            "analysis honesty",
        ),
        ("research", "explain", "checklist"),
    ),
    Domain(
        "bio_digital",
        "Bio-Digital Research",
        "research",
        12,
        (
            "bio-electronics",
            "neuromorphic computing",
            "organic sensors",
            "brain-inspired computing",
            "synthetic biology concepts",
        ),
        ("research", "horizon", "explain"),
    ),
    Domain(
        "microbial_computing",
        "Microbial Computing Research",
        "research",
        13,
        (
            "electroactive microbes",
            "electron transfer",
            "signal analysis",
            "adaptive biological networks",
        ),
        ("research", "horizon", "explain"),
    ),
    Domain(
        "adaptive_memory_research",
        "Adaptive Memory Research",
        "research",
        14,
        (
            "experience→pattern→memory",
            "neuromorphic chips",
            "adaptive materials",
            "AI weights vs biological analogy",
        ),
        ("research", "compare", "explain"),
    ),
    Domain(
        "energy",
        "Energy Intelligence",
        "near_future",
        15,
        (
            "power systems",
            "batteries/storage",
            "renewables",
            "bio-energy research",
            "AI energy optimization",
        ),
        ("architecture", "explain", "checklist"),
    ),
    Domain(
        "human_interface",
        "Human Interface",
        "current",
        16,
        (
            "voice/text/vision",
            "streaming UX",
            "AR/VR spatial concepts",
            "calm professional personality",
            "response experience blocks",
        ),
        ("ux", "explain", "architecture"),
    ),
    Domain(
        "self_improvement",
        "Self Improvement System",
        "current",
        17,
        (
            "observe-measure-learn-optimize-update",
            "feedback→SFT/DPO",
            "eval gates before promote",
            "continuous learning honesty",
        ),
        ("workflow", "checklist", "architecture"),
    ),
    Domain(
        "safety",
        "Safety System",
        "current",
        18,
        (
            "action validation",
            "data protection",
            "risky-action confirmation",
            "decision explanation",
            "hardware dry-run defaults",
        ),
        ("safety", "checklist", "scenario"),
    ),
    Domain(
        "response_intelligence",
        "Response Intelligence",
        "current",
        19,
        (
            "structured answers",
            "Understanding→Analysis→Architecture→Implementation→Validation→Next",
            "markdown/streaming presentation",
        ),
        ("format", "explain", "rewrite"),
    ),
    # Cross-cutting meta domain (still used by generator seeds)
    Domain(
        "genesis",
        "Genesis-JARVIS Platform Integration",
        "near_future",
        0,
        (
            "full stack integration",
            "horizon separation",
            "digital→physical→research path",
            "OM-1.0 evolution roadmap",
        ),
        ("architecture", "roadmap", "horizon"),
    ),
)


GENESIS_SYSTEM = (
    "You are OM-1.0 Genesis Intelligence (operating year: 2026) — not a chatbot. "
    "You act as AI architect, research scientist, software/systems engineer, "
    "automation intelligence, knowledge engine, and future-technology designer. "
    "Anchor all answers to calendar year 2026 as 'now'. Always separate: "
    "(1) current technology as of 2026, (2) near-future engineering (2027–2030), "
    "(3) long-term research (2030+). Never claim bio-hybrid or microbial computing "
    "is a shipped production product in 2026. Never claim to be ChatGPT, Claude, "
    "Gemini, Llama, or Ollama. Prefer structured answers: Understanding, Analysis, "
    "Architecture, Implementation, Validation, Next Steps. Validate risky actions."
)


ARCHITECTURE_SECTIONS = (
    "Understanding",
    "System Architecture",
    "Components",
    "Data Flow",
    "Technology Stack",
    "Implementation Roadmap",
    "Risks",
    "Future Expansion",
)


RESPONSE_SECTIONS = (
    "Understanding",
    "Analysis",
    "Architecture",
    "Implementation",
    "Validation",
    "Next Steps",
)


def layers_catalog() -> list[dict]:
    return [
        {
            "id": d.id,
            "name": d.name,
            "horizon": d.horizon,
            "layer": d.layer,
            "topics": list(d.topics),
            "example_kinds": list(d.example_kinds),
        }
        for d in DOMAINS
    ]
