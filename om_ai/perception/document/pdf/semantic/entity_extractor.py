"""Extract simple domain entities from PDF text."""
from __future__ import annotations


class EntityExtractor:
    def extract(self, text: str) -> dict[str, str]:
        entities: dict[str, str] = {}
        text_lower = (text or "").lower()

        # Separate keys so revenue + profit are both kept
        if "revenue" in text_lower:
            entities["revenue"] = "revenue"

        if "profit" in text_lower:
            entities["profit"] = "profit"

        if "invoice" in text_lower:
            entities["document"] = "invoice"

        if "agreement" in text_lower or "contract" in text_lower:
            entities["document"] = "contract"

        return entities
