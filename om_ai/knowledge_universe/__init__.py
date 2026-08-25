"""OM Universal Knowledge Universe — massive corpus layout + ingest hooks.

Folders match the completion roadmap (books, papers, programming, …).
Cleaning/dedupe/quality reuse ``om_ai.data_pipeline`` stages.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_ROOT = Path("data/om-knowledge-universe-v1")

UNIVERSE_BUCKETS: tuple[str, ...] = (
    "books",
    "scientific_papers",
    "programming",
    "mathematics",
    "engineering",
    "medicine",
    "history",
    "business",
    "patents",
    "documentation",
    "research",
    "code_repositories",
)

PIPELINE_STAGES: tuple[str, ...] = (
    "raw",
    "cleaned",
    "deduplicated",
    "filtered",
    "metadata",
    "chunked",
    "embeddings",
)


def init_universe(root: str | Path = DEFAULT_ROOT) -> dict[str, Any]:
    root = Path(root)
    created = 0
    for bucket in UNIVERSE_BUCKETS:
        for stage in PIPELINE_STAGES:
            p = root / "knowledge" / bucket / stage
            p.mkdir(parents=True, exist_ok=True)
            created += 1
        readme = root / "knowledge" / bucket / "README.md"
        if not readme.exists():
            readme.write_text(
                f"# {bucket.replace('_', ' ').title()}\n\n"
                "Drop **licensed** sources into `raw/`.\n\n"
                "Pipeline: raw → cleaned → deduplicated → filtered → "
                "metadata → chunked → embeddings → RAG ingest.\n",
                encoding="utf-8",
            )
    for extra in ("audit", "train", "manifests"):
        (root / extra).mkdir(parents=True, exist_ok=True)
    status = {
        "name": "om-knowledge-universe-v1",
        "priority": "highest",
        "buckets": list(UNIVERSE_BUCKETS),
        "pipeline": list(PIPELINE_STAGES),
        "paths_created": created,
        "next": [
            "Add licensed docs under knowledge/<bucket>/raw/",
            "om-ai data-pipeline run (or universe process)",
            "Ingest chunks into PersistentKnowledgeBase RAG",
            "Generate SFT from high-quality excerpts",
        ],
        "honesty": (
            "Layout + pipeline hooks ≠ filled corpus. "
            "Volume and licenses must be supplied by operators."
        ),
    }
    man = root / "manifest.json"
    man.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    (root / "audit" / "init.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    return {"root": str(root), **status}


def universe_status(root: str | Path = DEFAULT_ROOT) -> dict[str, Any]:
    root = Path(root)
    counts: dict[str, dict[str, int]] = {}
    total_raw = 0
    for bucket in UNIVERSE_BUCKETS:
        raw = root / "knowledge" / bucket / "raw"
        n = 0
        if raw.is_dir():
            n = sum(1 for p in raw.rglob("*") if p.is_file())
        total_raw += n
        counts[bucket] = {"raw_files": n}
    return {
        "root": str(root),
        "total_raw_files": total_raw,
        "buckets": counts,
        "ready_for_rag": total_raw > 0,
        "manifest_exists": (root / "manifest.json").is_file(),
    }


def process_stub(root: str | Path = DEFAULT_ROOT) -> dict[str, Any]:
    """Record a process plan; full clean/dedupe uses data_pipeline on each bucket later."""
    root = Path(root)
    init_universe(root)
    plan = {
        "stages": list(PIPELINE_STAGES),
        "actions": {
            "cleaned": "normalize text, strip boilerplate",
            "deduplicated": "exact + near-dup hash",
            "filtered": "quality + language + PII gates",
            "metadata": "title, license, domain, year",
            "chunked": "token-aware chunks for RAG",
            "embeddings": "hash/TF-IDF now; dense vectors when GPU allows",
        },
        "status": universe_status(root),
        "note": "Wire bucket paths into om_ai.data_pipeline / knowledge.rag as volume arrives.",
    }
    out = root / "audit" / "process_plan.json"
    out.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return plan
