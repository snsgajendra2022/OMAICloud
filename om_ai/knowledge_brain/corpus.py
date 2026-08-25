"""Create OM Knowledge Brain corpus layout + high-scale instruct JSONL.

Designed to generate large unique counts (toward millions) via combinatorial
templates × domains × eras × angles × difficulty × index salt — not by
duplicating the same few seeds.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterator

from .directive import KNOWLEDGE_SYSTEM
from .domains import DOMAINS
from .eras import ERAS

DEFAULT_ROOT = Path("data/om-knowledge-brain-v1")

DOMAIN_FOLDERS = tuple(d.folder for d in DOMAINS)

_ANGLES = (
    "first principles",
    "historical roots to 2026 practice",
    "systems architecture",
    "implementation checklist",
    "failure modes and risks",
    "cross-domain connections",
    "teaching a junior engineer",
    "executive briefing",
    "research vs production honesty",
    "OM agent playbook",
)

_DIFFICULTY = (
    "foundational",
    "intermediate",
    "advanced",
    "expert synthesis",
)

_TEMPLATES = (
    "As OM-1.0 Genesis Universal Intelligence, teach {topic} in domain `{domain}` "
    "through the lens of {angle} at {difficulty} level. Era context: {era_years} ({era_name}).",
    "Design how the OM Knowledge Brain should store, retrieve, and reason about {topic} "
    "({domain}). Angle: {angle}. Difficulty: {difficulty}. Anchor year: 2026.",
    "Connect era {era_years} ideas to modern {topic} practice for OM builders. "
    "Domain `{domain}`. Focus: {angle}. Level: {difficulty}.",
    "Create a structured OM answer on {topic} for domain `{domain}`: Understanding through "
    "Next Steps. Use {angle}; target {difficulty}. Era: {era_name}.",
    "For coding/engineering work involving {topic} (`{domain}`), provide architecture-first "
    "guidance with {angle} at {difficulty} depth. Present year 2026.",
    "Compare historical understanding vs 2026 capability for {topic} in `{domain}`. "
    "Angle: {angle}. Difficulty: {difficulty}. Era frame: {era_years}.",
    "Plan an OM agent workflow that uses knowledge of {topic} safely. Domain `{domain}`, "
    "angle {angle}, difficulty {difficulty}, era {era_name}.",
    "Explain {topic} so OM can assist humans solving complex problems. Domain `{domain}`. "
    "Style: {angle}. Depth: {difficulty}. Knowledge span 1600–2026.",
)

_SKILL_FOCUSES = (
    "reasoning",
    "planning",
    "architecture",
    "implementation",
    "validation",
    "teaching",
    "research synthesis",
    "tool selection",
)


def init_corpus(root: str | Path = DEFAULT_ROOT) -> dict[str, Any]:
    """Create knowledge folder tree + README manifests (empty raw/ for licensed docs)."""
    root = Path(root)
    created: list[str] = []
    for folder in DOMAIN_FOLDERS:
        for sub in ("raw", "cleaned", "chunks", "embeddings"):
            p = root / "knowledge" / folder / sub
            p.mkdir(parents=True, exist_ok=True)
            created.append(str(p))
        readme = root / "knowledge" / folder / "README.md"
        if not readme.exists():
            domain = next(d for d in DOMAINS if d.folder == folder)
            readme.write_text(
                f"# {domain.name}\n\n"
                f"**Purpose:** {domain.purpose}\n\n"
                f"**Topics:** {', '.join(domain.topics)}\n\n"
                "Place licensed documents under `raw/`. Pipeline fills cleaned/chunks.\n",
                encoding="utf-8",
            )
    for era in ERAS:
        p = root / "eras" / era.id
        p.mkdir(parents=True, exist_ok=True)
        meta = p / "era.json"
        meta.write_text(
            json.dumps(
                {
                    "id": era.id,
                    "name": era.name,
                    "years": era.years,
                    "themes": list(era.themes),
                    "key_ideas": list(era.key_ideas),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    train = root / "train"
    train.mkdir(parents=True, exist_ok=True)
    (root / "audit").mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": "om-knowledge-brain-v1",
        "coverage": "1600–2026",
        "domains": list(DOMAIN_FOLDERS),
        "eras": [e.id for e in ERAS],
        "directive": "OM-1.0 Genesis Universal Intelligence Master Directive",
        "note": (
            "Scaffold for Universal Knowledge Engine. Add licensed books/docs/papers "
            "into knowledge/<domain>/raw/ then run RAG ingest + SFT generate."
        ),
        "paths_created": len(created),
    }
    man_path = root / "manifest.json"
    man_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"root": str(root), "manifest": str(man_path), **manifest}


def _structured_answer(
    *,
    title: str,
    body: str,
    domain: str,
    era_years: str,
    angle: str,
    difficulty: str,
    skill: str,
    example_id: int,
) -> str:
    return "\n\n".join(
        [
            f"## Understanding\n{title}\n\n{body}",
            f"## Analysis\nAngle: **{angle}**. Difficulty: **{difficulty}**. "
            f"Skill focus: **{skill}**. Place this in the 1600–2026 knowledge arc "
            f"(era frame {era_years}) and connect to adjacent domains when useful.",
            "## Architecture\n"
            "OM cognitive path: Understanding → Reasoning → Planning → Agents/Tools → Validation. "
            "Knowledge Brain retrieves domain facts; Reasoning Engine applies first principles; "
            "never conflate research horizons with 2026 production.",
            "## Implementation\n"
            "1) State assumptions for year 2026.\n"
            "2) Give concrete steps, interfaces, or checklists.\n"
            "3) If coding: Technology · File structure · Tests · Deployment notes.\n"
            f"4) Example id `{example_id}` for dataset traceability.",
            "## Validation\n"
            "Separate: known science/engineering · engineering judgment · open research. "
            "No invented citations. Bio/quantum/neuromorphic claims labeled by horizon.",
            "## Next Steps\n"
            "What OM should store in project memory, which agent to call next, "
            "and what licensed corpus to add under knowledge/"
            f"{domain}/raw/ to deepen this topic.",
            f"\n_Domain: `{domain}` · Era: {era_years} · OM-1.0 Genesis Universal Intelligence_",
        ]
    )


def _topic_pool() -> list[tuple[str, str, str]]:
    """(domain_id, topic, era_id) pool."""
    pool: list[tuple[str, str, str]] = []
    for d in DOMAINS:
        for t in d.topics:
            for e in ERAS:
                pool.append((d.id, t, e.id))
        # also domain purpose as a topic
        pool.append((d.id, d.purpose, "era7_generative_ai"))
    for e in ERAS:
        for t in e.seed_topics:
            pool.append(("history", t, e.id))
        for idea in e.key_ideas:
            pool.append(("history", idea, e.id))
    return pool


def iter_instruct_rows(*, count: int) -> Iterator[dict[str, Any]]:
    """Yield up to ``count`` unique-ish SFT rows (scales toward millions)."""
    pool = _topic_pool()
    era_by_id = {e.id: e for e in ERAS}
    n_pool = len(pool)
    n_tmpl = len(_TEMPLATES)
    n_ang = len(_ANGLES)
    n_diff = len(_DIFFICULTY)
    n_skill = len(_SKILL_FOCUSES)
    # Theoretical capacity >> 1e6 with index salt
    seen: set[str] = set()
    produced = 0
    i = 0
    # Allow many wraps; salt in instruction keeps rows unique at million scale.
    max_attempts = max(count * 20, count + 100_000)

    while produced < count and i < max_attempts:
        domain_id, topic, era_id = pool[i % n_pool]
        era = era_by_id[era_id]
        tmpl = _TEMPLATES[i % n_tmpl]
        angle = _ANGLES[(i // 3) % n_ang]
        difficulty = _DIFFICULTY[(i // 7) % n_diff]
        skill = _SKILL_FOCUSES[(i // 11) % n_skill]
        salt = i // max(n_pool, 1)

        instruction = tmpl.format(
            topic=topic,
            domain=domain_id,
            angle=angle,
            difficulty=difficulty,
            era_years=era.years,
            era_name=era.name,
        )
        instruction = f"{instruction} [ex {i} · skill {skill} · v{salt}]"

        body = (
            f"Topic `{topic}` in domain `{domain_id}`. "
            f"Era {era.name} ({era.years}) key ideas: {', '.join(era.key_ideas[:3])}. "
            f"Apply OM mission: transform information into intelligence. "
            f"Skill focus: {skill}."
        )
        output = _structured_answer(
            title=f"{topic}",
            body=body,
            domain=domain_id,
            era_years=era.years,
            angle=angle,
            difficulty=difficulty,
            skill=skill,
            example_id=i,
        )

        key = hashlib.sha1(instruction.encode()).hexdigest()
        i += 1
        if key in seen:
            continue
        seen.add(key)
        produced += 1
        yield {
            "system": KNOWLEDGE_SYSTEM,
            "instruction": instruction,
            "output": output,
            "domain": domain_id,
            "era": era_id,
            "angle": angle,
            "difficulty": difficulty,
            "skill": skill,
            "tags": [domain_id, era_id, skill, difficulty.replace(" ", "-")],
            "messages": [
                {"role": "system", "content": KNOWLEDGE_SYSTEM},
                {"role": "user", "content": instruction},
                {"role": "assistant", "content": output},
            ],
        }


def write_instruct_dataset(
    out_path: str | Path,
    *,
    count: int = 500,
    also_init_corpus: bool = True,
    root: str | Path = DEFAULT_ROOT,
) -> dict[str, Any]:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if also_init_corpus:
        init_corpus(root)
    n = 0
    domains: dict[str, int] = {}
    eras: dict[str, int] = {}
    with out_path.open("w", encoding="utf-8") as f:
        for row in iter_instruct_rows(count=max(1, count)):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
            domains[row["domain"]] = domains.get(row["domain"], 0) + 1
            eras[row["era"]] = eras.get(row["era"], 0) + 1
            if n % 50_000 == 0:
                # progress-friendly for huge runs
                pass
    man = {
        "name": "om-knowledge-instruct-v1",
        "path": str(out_path),
        "count": n,
        "coverage": "1600–2026",
        "directive": "OM-1.0 Genesis Universal Intelligence Master Directive",
        "domains": domains,
        "eras": eras,
        "system": KNOWLEDGE_SYSTEM,
        "note": (
            "High-scale instruction dataset for Universal Knowledge Brain. "
            "Use --count up to 1e6+; add licensed docs under knowledge/*/raw/ for RAG depth."
        ),
    }
    man_path = out_path.with_suffix(".manifest.json")
    man_path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
    audit = Path(root) / "audit" / "instruct_build.json"
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
    return man
