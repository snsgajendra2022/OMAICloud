"""STEP 94.11 — Curriculum Generator.

Build progressive question curricula for teacher distillation by domain and level.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any


def _repo_data() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "om_distillation" / "curriculum"


_TEMPLATES: dict[str, dict[str, list[str]]] = {
    "software": {
        "foundational": [
            "What is {topic} and when should you use it?",
            "Explain the core building blocks of {topic}.",
            "Compare {topic} with a common alternative.",
        ],
        "intermediate": [
            "Design a production-ready {topic} architecture with trade-offs.",
            "How do you test and observe a {topic} system?",
            "What failure modes appear when scaling {topic}?",
        ],
        "advanced": [
            "Build a multi-tenant {topic} design with isolation and permissions.",
            "Write a step-by-step migration plan for introducing {topic}.",
            "How would you harden {topic} for security and compliance?",
        ],
        "systems": [
            "Create an end-to-end roadmap to ship {topic} across teams.",
            "Define SLOs, queues, and rollback strategy for a {topic} platform.",
        ],
    },
    "devops": {
        "foundational": [
            "Explain {topic} architecture in plain language.",
            "What problems does {topic} solve in deployment?",
        ],
        "intermediate": [
            "Design a CI/CD flow that uses {topic} safely.",
            "How do networking and storage work in {topic}?",
        ],
        "advanced": [
            "Plan multi-cluster {topic} with observability and policy controls.",
            "How do you recover from a failed {topic} rollout?",
        ],
        "systems": [
            "Create an organization-wide {topic} operating model with roles and runbooks.",
        ],
    },
    "security": {
        "foundational": [
            "Explain authentication vs authorization for {topic}.",
            "What are common security mistakes with {topic}?",
        ],
        "intermediate": [
            "Design least-privilege access for a {topic} system.",
            "How should secrets, audits, and encryption be handled in {topic}?",
        ],
        "advanced": [
            "Threat-model a multi-tenant {topic} deployment.",
        ],
        "systems": [
            "Define a security governance checklist for {topic} across an organization.",
        ],
    },
    "general": {
        "foundational": [
            "Explain {topic} clearly with examples.",
            "What are the key concepts behind {topic}?",
        ],
        "intermediate": [
            "Give a practical guide to applying {topic}.",
            "What trade-offs matter most for {topic}?",
        ],
        "advanced": [
            "Design a robust approach to {topic} with edge cases.",
        ],
        "systems": [
            "Create a roadmap to master and operationalize {topic}.",
        ],
    },
}

_LEVEL_ORDER = ("foundational", "intermediate", "advanced", "systems")


class CurriculumGenerator:
    """STEP 94.11 — generate distillation curricula."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root else _repo_data()
        self.root.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        topic: str,
        *,
        domain: str = "software",
        count: int = 10,
        start_level: str = "foundational",
    ) -> dict[str, Any]:
        topic = (topic or "general knowledge").strip()
        domain = domain if domain in _TEMPLATES else "general"
        start = start_level if start_level in _LEVEL_ORDER else "foundational"
        levels = _LEVEL_ORDER[_LEVEL_ORDER.index(start) :]
        questions: list[dict[str, Any]] = []
        i = 0
        while len(questions) < max(1, int(count)):
            level = levels[min(i // max(1, count // len(levels) or 1), len(levels) - 1)]
            templates = _TEMPLATES[domain][level]
            tmpl = templates[i % len(templates)]
            q = tmpl.format(topic=topic)
            questions.append(
                {
                    "id": f"q_{uuid.uuid4().hex[:8]}",
                    "question": q,
                    "domain": domain,
                    "level": level,
                    "topic": topic,
                    "priority": _LEVEL_ORDER.index(level) + 1,
                }
            )
            i += 1
            if i > count * 5:
                break

        pack = {
            "step": "94.11",
            "curriculum_id": f"cur_{uuid.uuid4().hex[:10]}",
            "topic": topic,
            "domain": domain,
            "count": len(questions),
            "questions": questions,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        out = self.root / f"{pack['curriculum_id']}.json"
        out.write_text(json.dumps(pack, indent=2), encoding="utf-8")
        pack["path"] = str(out)
        return pack

    def from_gaps(
        self,
        gaps: list[dict[str, Any]] | list[str],
        *,
        per_gap: int = 3,
        domain: str = "software",
    ) -> dict[str, Any]:
        """Expand knowledge gaps into a curriculum."""
        topics: list[str] = []
        for g in gaps or []:
            if isinstance(g, str):
                topics.append(g)
            elif isinstance(g, dict):
                topics.append(str(g.get("topic") or g.get("question") or g.get("gap") or "").strip())
        topics = [t for t in topics if t]
        all_q: list[dict[str, Any]] = []
        for topic in topics:
            part = self.generate(topic, domain=domain, count=per_gap, start_level="intermediate")
            all_q.extend(part.get("questions") or [])
        pack = {
            "step": "94.11",
            "curriculum_id": f"gaps_{uuid.uuid4().hex[:10]}",
            "topic": "knowledge_gaps",
            "domain": domain,
            "count": len(all_q),
            "questions": all_q,
            "source_gaps": topics,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        out = self.root / f"{pack['curriculum_id']}.json"
        out.write_text(json.dumps(pack, indent=2), encoding="utf-8")
        pack["path"] = str(out)
        return pack

    def status(self) -> dict[str, Any]:
        files = sorted(self.root.glob("*.json"))
        return {
            "step": "94.11",
            "name": "Curriculum Generator",
            "curricula": len(files),
            "path": str(self.root),
            "latest": [p.name for p in files[-5:]],
        }
