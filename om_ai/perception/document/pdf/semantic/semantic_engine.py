"""
OM AI PDF Semantic Understanding Engine

Responsible for:
- Document classification
- Entity extraction
- Insight generation
- Knowledge graph creation
"""

from __future__ import annotations

from typing import Any

from .classifier import DocumentClassifier
from .entity_extractor import EntityExtractor
from .insight_engine import InsightEngine

# Use knowledge.graph engine — it exposes process(entities, source)
from om_ai.knowledge.graph.engine import KnowledgeGraphEngine


class SemanticEngine:
    def __init__(self) -> None:
        self.classifier = DocumentClassifier()
        self.entity_extractor = EntityExtractor()
        self.insight_engine = InsightEngine()
        self.knowledge_graph = KnowledgeGraphEngine()

    def understand(self, text: str) -> dict[str, Any]:
        text = text or ""

        # 1. Detect document type
        document_type = self.classifier.classify(text)

        # 2. Extract entities (always a dict)
        entities = self.entity_extractor.extract(text)
        if entities is None:
            entities = {}

        # 3. Generate insights
        insights = self.insight_engine.analyze(entities)
        if insights is None:
            insights = []

        # 4. Create knowledge graph
        graph = self.knowledge_graph.process(entities, "pdf")

        return {
            "document_type": document_type,
            "entities": entities,
            "insights": insights,
            "knowledge_graph": graph,
        }
