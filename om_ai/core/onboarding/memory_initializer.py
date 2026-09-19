"""Seed personal memory from onboarding profile."""
from __future__ import annotations

from typing import Any


class MemoryInitializer:
    def initialize(
        self,
        tenant_id: str,
        actor: str,
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        purpose = str(profile.get("purpose") or "general")
        style = str(profile.get("response_style") or profile.get("style") or "balanced")
        language = str(profile.get("language") or "en")
        display = str(profile.get("display_name") or "User")

        likes: list[str] = []
        if "technical" in style.lower() or purpose in {"coding", "ai development"}:
            likes.extend(
                [
                    "detailed technical answers",
                    "architecture discussion",
                    "production-ready code",
                ]
            )
        elif purpose == "business":
            likes.extend(["clear strategy", "professional tone", "actionable plans"])
        elif purpose == "personal":
            likes.extend(["warm human replies", "practical daily help"])
        else:
            likes.append("clear helpful answers")

        if language in {"hi", "hi-en"}:
            likes.append("Hinglish / Hindi-friendly conversation")

        facts = [
            f"User display name: {display}",
            f"Purpose: {purpose}",
            f"Preferred style: {style}",
            f"Preferred language: {language}",
            "User likes: " + "; ".join(likes),
        ]

        memory = {
            "tenant_id": tenant_id,
            "user": actor,
            "purpose": purpose,
            "communication_style": style,
            "language": language,
            "companion_enabled": True,
            "facts": facts,
            "likes": likes,
            "preferences": dict(profile.get("preferences") or {}),
        }

        # Soft-write into human memory + companion preference if available
        try:
            from om_ai.core.human_memory import get_human_memory

            hm = get_human_memory()
            if hasattr(hm, "semantic") and hasattr(hm.semantic, "set"):
                hm.semantic.set("user_name", display)
                hm.semantic.set("detail_preference", str((memory["preferences"] or {}).get("detail") or "balanced"))
                hm.semantic.set("active_project", "OM AI" if "ai" in purpose else purpose)
            if hasattr(hm, "preferences") and hasattr(hm.preferences, "observe"):
                hm.preferences.observe(f"I like {style} answers")
        except Exception:
            pass

        return memory
