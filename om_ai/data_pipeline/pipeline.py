"""End-to-end OMAI-Corpus-v1 pipeline runner."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .validator import ensure_layout, validate_corpus


# Map raw category folders → roadmap ``sources/`` names
_RAW_TO_SOURCES = {
    "wikipedia": "wikipedia",
    "books": "books",
    "code": "code",
    "papers": "science",
    "conversations": "conversations",
    "fineweb": "custom",
}


def sync_sources_from_raw(root: Path) -> dict[str, int]:
    """Mirror ``raw/{cat}/*`` into ``sources/{mapped}/`` for the roadmap layout."""
    counts: dict[str, int] = {}
    raw = root / "raw"
    if not raw.is_dir():
        return counts
    for raw_name, src_name in _RAW_TO_SOURCES.items():
        src = raw / raw_name
        dst = root / "sources" / src_name
        dst.mkdir(parents=True, exist_ok=True)
        n = 0
        if src.is_dir():
            for path in src.glob("*.jsonl"):
                target = dst / path.name
                shutil.copy2(path, target)
                n += 1
        counts[src_name] = n
    return counts


class DataPipeline:
    """Named stages matching the Own Model Roadmap."""

    def __init__(self, root: str | Path = "data/omai-corpus-v1"):
        self.root = Path(root)

    def run(
        self,
        *,
        fetch: bool = True,
        source_ids: list[str] | None = None,
        max_docs: int = 40,
        tokenize: bool = True,
    ) -> dict[str, Any]:
        return run_omai_corpus_v1(
            self.root,
            fetch=fetch,
            source_ids=source_ids,
            max_docs=max_docs,
            tokenize=tokenize,
        )


def run_omai_corpus_v1(
    root: str | Path = "data/omai-corpus-v1",
    *,
    fetch: bool = True,
    source_ids: list[str] | None = None,
    max_docs: int = 40,
    tokenize: bool = True,
) -> dict[str, Any]:
    from om_ai.corpus.omai_v1 import build_omai_corpus_v1

    root = ensure_layout(root)
    audit = build_omai_corpus_v1(
        root,
        fetch=fetch,
        source_ids=source_ids,
        max_docs=max_docs,
        tokenize=tokenize,
    )
    sources_synced = sync_sources_from_raw(root)
    validation = validate_corpus(root)
    audit = {
        **audit,
        "sources_synced": sources_synced,
        "layout_validation": validation,
        "pipeline": "om_ai.data_pipeline",
        "flow": [
            "raw",
            "cleaner",
            "language_filter",
            "quality",
            "deduplicator",
            "tokenizer",
            "train/validation",
        ],
    }
    audit_path = root / "audit" / "build_report.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    import json

    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return audit
