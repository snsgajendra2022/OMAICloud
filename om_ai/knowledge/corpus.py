"""Knowledge corpus layout helpers (science/engineering/... buckets)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

BUCKETS = (
    "science",
    "engineering",
    "programming",
    "ai",
    "history",
    "business",
    "mathematics",
    "robotics",
    "electronics",
)


def ensure_corpus_layout(root: str | Path | None = None) -> dict[str, Any]:
    root = Path(root or Path.cwd()).resolve()
    base = root / "data" / "om-knowledge-corpus" / "knowledge"
    created: list[str] = []
    for b in BUCKETS:
        d = base / b / "raw"
        d.mkdir(parents=True, exist_ok=True)
        readme = base / b / "README.md"
        if not readme.is_file():
            readme.write_text(
                f"# {b.replace('_', ' ').title()} corpus\n\nPlace licensed sources under `raw/`.\n",
                encoding="utf-8",
            )
            created.append(str(readme))
    for sub in ("ingestion", "embeddings", "retrieval", "knowledge_graph"):
        (root / "data" / "om-knowledge-corpus" / sub).mkdir(parents=True, exist_ok=True)
    return {
        "root": str(base),
        "buckets": list(BUCKETS),
        "created_readmes": created,
        "ok": True,
    }
