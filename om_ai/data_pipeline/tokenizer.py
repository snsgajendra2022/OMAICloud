"""Corpus tokenization helpers (production OM tokenizer)."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def encode_corpus_texts(
    texts: list[str],
    *,
    tokenizer_path: str | Path = "artifacts/tokenizer-production-65536.json",
) -> dict[str, Any]:
    from om_ai.tokenizer import load_tokenizer

    tok = load_tokenizer(str(tokenizer_path))
    total = 0
    heads: list[list[int]] = []
    for text in texts:
        ids = tok.encode(text, add_eos=True)
        total += len(ids)
        heads.append(ids[:64])
    return {
        "tokenizer": str(tokenizer_path),
        "docs": len(texts),
        "tokens": total,
        "ids_heads": heads[:5],
    }
