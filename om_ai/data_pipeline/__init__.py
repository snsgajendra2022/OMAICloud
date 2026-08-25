"""OMAI data pipeline — Milestone 1 factory for OMAI-Corpus-v1.

Thin, named stages over ``om_ai.corpus`` so the Own Model Roadmap maps 1:1::

    Raw → Cleaner → Language → Quality → Dedup → Tokenizer → Train/Val
"""
from __future__ import annotations

from .pipeline import DataPipeline, run_omai_corpus_v1

__all__ = ["DataPipeline", "run_omai_corpus_v1"]
