"""Download / fetch licensed sources into OMAI-Corpus-v1."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from om_ai.corpus.omai_v1 import fetch_sources


def download_sources(
    root: str | Path = "data/omai-corpus-v1",
    *,
    source_ids: list[str] | None = None,
    max_docs: int = 40,
) -> list[dict[str, Any]]:
    results = fetch_sources(Path(root), source_ids, max_docs=max_docs)
    return [
        {
            "source_id": r.source_id,
            "path": r.path,
            "docs": r.docs,
            "bytes": r.bytes,
            "ok": r.ok,
            "detail": r.detail,
        }
        for r in results
    ]
