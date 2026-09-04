"""Generate insights from extracted PDF entities."""
from __future__ import annotations


class InsightEngine:
    def analyze(self, entities: dict | None) -> list[str]:
        insights: list[str] = []
        entities = entities or {}
        values = {str(v).lower() for v in entities.values()}
        keys = {str(k).lower() for k in entities}

        if "revenue" in values or "revenue" in keys:
            insights.append("Revenue information detected")

        if "profit" in values or "profit" in keys:
            insights.append("Profit information detected")

        if "invoice" in values:
            insights.append("Invoice document signals detected")

        if "contract" in values:
            insights.append("Legal/contract signals detected")

        return insights
