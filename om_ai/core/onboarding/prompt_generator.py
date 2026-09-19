"""Generate starter prompts personalized to purpose / language."""
from __future__ import annotations

from typing import Any


_TEMPLATES: dict[str, list[str]] = {
    "coding": [
        "Debug this Python error",
        "Review architecture",
        "Create API design",
        "Optimize performance",
    ],
    "ai development": [
        "Review OM architecture",
        "Debug Python pipeline",
        "Design AI system",
        "Optimize response quality",
        "Plan companion voice upgrade",
    ],
    "business": [
        "Create business plan",
        "Analyze strategy",
        "Write professional email",
    ],
    "personal": [
        "Plan my day",
        "Create habits",
        "Organize tasks",
    ],
    "general": [
        "Explain simply",
        "Create action plan",
        "Help me think this through",
    ],
}


class PromptGenerator:
    def generate(
        self,
        tenant_id: str,
        actor: str,
        profile: dict[str, Any],
    ) -> list[dict[str, Any]]:
        purpose = str(profile.get("purpose") or "general").lower()
        titles = list(_TEMPLATES.get(purpose) or _TEMPLATES["general"])
        if "ai" in purpose and "develop" in purpose and purpose not in _TEMPLATES:
            titles = list(_TEMPLATES["ai development"])

        language = str(profile.get("language") or "en")
        if language in {"hi", "hi-en"}:
            titles = titles + ["Hinglish mein samjhao", "Project plan banao"]

        return [
            {
                "tenant_id": tenant_id,
                "user_id": actor,
                "title": title,
                "body": title,
            }
            for title in titles
        ]
