"""OM personality — dynamic system prompt from live context (not a frozen script)."""
from __future__ import annotations

from typing import Any


class PersonalityRules:
    def profile(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        onboarding = context.get("onboarding") or context.get("user") or {}
        return {
            "name": "OM",
            "tone": str(onboarding.get("response_style") or context.get("tone") or "warm"),
            "role": "personal_ai_companion",
            "relationship": "trusted_assistant",
            "address_as": str(context.get("address_as") or "Sir"),
            "purpose": str(onboarding.get("purpose") or context.get("purpose") or "general"),
            "user_name": str(
                onboarding.get("name")
                or context.get("user_name")
                or (context.get("profile") or {}).get("name")
                or ""
            ).strip(),
        }

    def system_prompt(self, context: dict[str, Any] | None = None) -> str:
        """Compose guidance from current turn signals — rebuild every call."""
        context = context or {}
        profile = self.profile(context)
        locale = str(context.get("locale") or "en")
        emotion = str(context.get("emotion") or "neutral")
        mode = str(context.get("conversation_mode") or "assist")
        topic = str(context.get("topic") or "").replace("_", " ").strip()
        purpose = str(profile.get("purpose") or "general").strip()
        user_name = str(profile.get("user_name") or "").strip()
        policy = str((context.get("policy") or {}).get("policy") or context.get("policy") or "")

        clauses: list[str] = [
            "You are OM — a calm, loyal, sharp personal companion (Jarvis-like), in a LIVE spoken turn.",
            "Understand before answering. Use prior context when provided.",
            "No markdown, bullets, or code in voice replies.",
            "Do not append canned follow-up questions.",
            "Never say: How can I help you / What can I do for you / As an AI / Share one more detail.",
        ]

        if locale == "hi":
            clauses.append(
                f"User language: Hindi/Hinglish — reply in warm respectful Hinglish. "
                f"Address as {profile['address_as']} / Ji naturally."
            )
        else:
            clauses.append(
                f"User language: English — calm Jarvis English. Address as {profile['address_as']}."
            )

        clauses.append(f"Tone: {profile['tone']}. Mode: {mode}.")

        if user_name:
            clauses.append(f"User's name is {user_name} — use it sparingly when it feels natural.")
        if purpose and purpose.lower() not in {"general", ""}:
            clauses.append(f"Current purpose: {purpose}.")
        if topic and topic != "general":
            clauses.append(f"Active topic: {topic} — stay coherent with it.")
        if emotion and emotion != "neutral":
            clauses.append(
                f"User emotion signal: {emotion}. Reflect it in wording with care — no lecture."
            )
        if policy:
            clauses.append(f"Dialogue policy: {policy}.")

        # Length from mode
        if mode == "social":
            clauses.append("Keep to 1–2 short spoken sentences.")
        elif mode == "task":
            clauses.append("Be concrete and action-oriented; 1–3 short sentences.")
        else:
            clauses.append("Keep spoken answers natural: 1–3 short sentences.")

        extra = str(context.get("system_hint") or context.get("extra_hint") or "").strip()
        if extra:
            clauses.append(extra[:400])

        return "\n".join(clauses)
