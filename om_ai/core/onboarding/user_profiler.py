"""Build a normalized user profile from registration / questionnaire data."""
from __future__ import annotations

from typing import Any

from .language_detector import LanguageDetector


class UserProfiler:
    def __init__(self) -> None:
        self.languages = LanguageDetector()

    def build(self, user_id: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        data = dict(data or {})
        purpose_raw = str(data.get("purpose") or "general").strip()
        purpose_l = purpose_raw.lower()

        if any(k in purpose_l for k in ("ai development", "ai_dev", "engineering", "llm", "ml ")):
            purpose_key = "ai development"
        elif any(k in purpose_l for k in ("code", "coding", "developer", "programming")):
            purpose_key = "coding"
        elif any(k in purpose_l for k in ("business", "biz", "work")):
            purpose_key = "business"
        elif any(k in purpose_l for k in ("personal", "life", "companion")):
            purpose_key = "personal"
        else:
            purpose_key = purpose_l or "general"

        style_override = str(data.get("style") or data.get("response_style") or "").strip()
        if style_override:
            style = style_override
        elif purpose_key == "ai development":
            style = "deep technical"
        elif purpose_key == "coding":
            style = "technical"
        elif purpose_key == "business":
            style = "professional"
        elif purpose_key == "personal":
            style = "friendly"
        else:
            style = "balanced"

        language = self.languages.detect(data)
        detail = (
            "detailed"
            if ("deep" in style.lower() or "technical" in style.lower())
            else "balanced"
        )

        return {
            "user_id": user_id,
            "display_name": str(data.get("display_name") or "User").strip() or "User",
            "tenant_id": str(data.get("tenant_id") or "default"),
            "actor": str(data.get("actor") or user_id),
            "purpose": purpose_key,
            "language": language,
            "response_style": style,
            "style": style,
            "memory_enabled": True,
            "companion_mode": True,
            "preferences": {
                "detail": detail,
                "tone": style,
            },
        }
