"""Historical eras for OM Knowledge Brain (1600–2026)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Era:
    id: str
    name: str
    years: str
    themes: tuple[str, ...]
    key_ideas: tuple[str, ...]
    seed_topics: tuple[str, ...]


ERAS: tuple[Era, ...] = (
    Era(
        "era1_scientific_revolution",
        "Scientific Revolution",
        "1600–1700",
        ("physics", "astronomy", "mathematics", "scientific method"),
        (
            "Galileo observation + experiment",
            "Kepler planetary laws",
            "Newton classical mechanics & gravity",
            "Early calculus & probability",
            "Telescope astronomy",
        ),
        (
            "Explain Newton's laws for engineers",
            "How did Kepler improve Copernicus?",
            "Why scientific method beats pure authority",
        ),
    ),
    Era(
        "era2_enlightenment",
        "Enlightenment + Industrial Foundation",
        "1700–1800",
        ("chemistry", "engineering", "philosophy", "mathematics"),
        (
            "Modern chemistry foundations",
            "Atomic concepts & reactions",
            "Mechanical systems & steam beginnings",
            "Advanced calculus & statistics",
            "Logic and scientific reasoning",
        ),
        (
            "Connect chemistry foundations to materials engineering",
            "How Enlightenment thinking shaped engineering",
            "Early industrial mechanical systems overview",
        ),
    ),
    Era(
        "era3_industrial",
        "Industrial Revolution",
        "1800–1900",
        ("engineering", "thermodynamics", "electromagnetism", "biology"),
        (
            "Steam engines & manufacturing",
            "Electricity & thermodynamics",
            "Maxwell electromagnetism",
            "Evolution & microbiology foundations",
            "Telegraph & telephone",
        ),
        (
            "Thermodynamics for energy systems",
            "Electromagnetism → communications path",
            "Industrial manufacturing as systems design",
        ),
    ),
    Era(
        "era4_modern_science",
        "Modern Science Foundation",
        "1900–1950",
        ("quantum", "relativity", "computing foundations", "electronics"),
        (
            "Relativity & quantum mechanics",
            "Einstein / Bohr / Heisenberg / Schrödinger",
            "Boolean logic & Turing machine",
            "Information theory",
            "Vacuum tubes & early computers",
        ),
        (
            "Relativity vs classical mechanics for engineers",
            "Turing machine as computing foundation",
            "Vacuum tube → early digital systems",
        ),
    ),
    Era(
        "era5_computer_revolution",
        "Computer Revolution",
        "1950–2000",
        ("hardware", "software", "networks", "AI history"),
        (
            "Transistor → IC → microprocessor",
            "Operating systems & networks",
            "Fortran/COBOL/C/C++/Java/Python/JS lineage",
            "Turing Test (1950), Dartmouth (1956)",
            "Expert systems → early ML",
        ),
        (
            "Hardware evolution vacuum tube to microprocessor",
            "Why C enabled portable systems software",
            "AI timeline 1950–2000 for OM training",
        ),
    ),
    Era(
        "era6_internet_ai",
        "Internet + AI Era",
        "2000–2020",
        ("web", "cloud", "big data", "deep learning"),
        (
            "HTML/CSS/JS/APIs/cloud",
            "Distributed systems, Hadoop, Spark",
            "Deep learning & GPU computing",
            "Mobile platforms",
            "Neural network renaissance",
        ),
        (
            "Cloud + API architecture for products",
            "Deep learning vs classical ML",
            "Web stack evolution for full-stack engineers",
        ),
    ),
    Era(
        "era7_generative_ai",
        "Generative AI Era",
        "2020–2026",
        ("transformers", "LLMs", "agents", "RAG", "multimodal"),
        (
            "Tokenizer → embedding → attention → layers → output",
            "Pretrain / SFT / RLHF / DPO",
            "RAG + tools + agents",
            "Multimodal systems",
            "OM-style cognitive OS around the LLM",
        ),
        (
            "Explain transformer stack for OM-1.0 engineers",
            "RAG vs fine-tuning vs pretraining tradeoffs",
            "Why OM AI is model + memory + agents + knowledge",
        ),
    ),
)


def eras_catalog() -> list[dict]:
    return [
        {
            "id": e.id,
            "name": e.name,
            "years": e.years,
            "themes": list(e.themes),
            "key_ideas": list(e.key_ideas),
            "seed_topics": list(e.seed_topics),
        }
        for e in ERAS
    ]
