"""Validate OMAI-Corpus-v1 layout + stage artifacts."""
from __future__ import annotations

from pathlib import Path
from typing import Any

REQUIRED_DIRS = (
    "sources/wikipedia",
    "sources/books",
    "sources/code",
    "sources/science",
    "sources/conversations",
    "sources/custom",
    "raw",
    "cleaned",
    "filtered",
    "deduplicated",
    "tokenized",
    "train",
    "validation",
)


def ensure_layout(root: str | Path) -> Path:
    root = Path(root)
    for rel in REQUIRED_DIRS:
        (root / rel).mkdir(parents=True, exist_ok=True)
    return root


def validate_corpus(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    missing = [rel for rel in REQUIRED_DIRS if not (root / rel).exists()]
    train = root / "train" / "corpus.txt"
    report = root / "audit" / "build_report.json"
    return {
        "ok": not missing and train.is_file(),
        "missing_dirs": missing,
        "has_train_txt": train.is_file(),
        "train_bytes": train.stat().st_size if train.is_file() else 0,
        "has_build_report": report.is_file(),
        "root": str(root),
    }
