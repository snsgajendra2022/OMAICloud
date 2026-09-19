"""Create personalized OM assistant identity + system prompt."""
from __future__ import annotations

from typing import Any


_NAMES = {
    "coding": "OM Developer",
    "ai development": "OM Engineering Companion",
    "ai_development": "OM Engineering Companion",
    "business": "OM Business Partner",
    "personal": "OM Companion",
    "general": "OM Assistant",
}


class AssistantInitializer:
    def create(
        self,
        tenant_id: str,
        actor: str,
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        purpose = str(profile.get("purpose") or "general").strip().lower()
        style = str(profile.get("response_style") or profile.get("style") or "balanced")
        language = str(profile.get("language") or "en")
        display = str(profile.get("display_name") or "User")
        name = _NAMES.get(purpose, _NAMES.get(purpose.replace(" ", "_"), "OM Assistant"))
        if "ai" in purpose and "develop" in purpose:
            name = "OM Engineering Companion"

        system_prompt = (
            f"You are {name}, the personal OM AI companion for {display}.\n"
            f"User purpose: {purpose}\n"
            f"Communication style: {style}\n"
            f"Preferred language: {language}\n\n"
            "Rules:\n"
            "- Understand context before answering\n"
            "- Remember preferences across turns\n"
            "- Speak naturally (English / Hindi / Hinglish as preferred)\n"
            "- Be proactive and precise\n"
            "- Match depth to the user's style (brief vs deep technical)\n"
        )

        return {
            "tenant_id": tenant_id,
            "user_id": actor,
            "name": name,
            "system_prompt": system_prompt.strip(),
            "language": language,
            "style": style,
            "created": True,
        }
