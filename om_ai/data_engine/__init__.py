"""
OM Data Engine

Responsible for:

- Dataset ingestion
- Cleaning
- Quality filtering
- Classification
- Training dataset creation
"""
from .factory import OMKnowledgeFactory

from .pipeline import (
    TextCleaner,
    Deduplicator,
    QualityScorer,
    KnowledgeClassifier,
)


__all__ = [
    "OMKnowledgeFactory",
    "TextCleaner",
    "Deduplicator",
    "QualityScorer",
    "KnowledgeClassifier",
]