"""OM Universal Knowledge Brain (1600–2026) — corpus + directive package.

Honest scope: this builds a *knowledge ecosystem* (domains, eras, RAG folders,
instruction rows). It does **not** magically inject all human knowledge into
model weights. Scale via licensed docs → RAG → SFT → larger pretrain.
"""
from __future__ import annotations

from .catalog import knowledge_catalog
from .corpus import init_corpus, write_instruct_dataset
from .directive import KNOWLEDGE_DIRECTIVE, KNOWLEDGE_SYSTEM
from .domains import DOMAINS
from .eras import ERAS

__all__ = [
    "DOMAINS",
    "ERAS",
    "KNOWLEDGE_DIRECTIVE",
    "KNOWLEDGE_SYSTEM",
    "knowledge_catalog",
    "init_corpus",
    "write_instruct_dataset",
]
