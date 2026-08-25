"""Training dataset helpers for OMAI-Corpus-v1."""
from __future__ import annotations

from pathlib import Path


def default_corpus_txt(root: str | Path = "data/omai-corpus-v1") -> Path:
    return Path(root) / "train" / "corpus.txt"


def resolve_train_data(path: str | Path | None = None) -> str:
    if path:
        return str(path)
    p = default_corpus_txt()
    if p.is_file():
        return str(p)
    raise FileNotFoundError("OMAI-Corpus-v1 train/corpus.txt missing — run data pipeline first")
