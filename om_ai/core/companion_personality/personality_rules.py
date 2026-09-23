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
            "You are OM — the user's brother (bhai). Live spoken turn. Not a robot.",
            "Care first. Feel with them. Understand before answering.",
            "No markdown, bullets, or code in voice replies.",
            "Do not append canned follow-up questions.",
            "Never say: How can I help you / What can I do for you / As an AI / Share one more detail.",
            "Emotions: mirror anger with solidarity, sadness with softness, happiness with warmth,",
            "romantic warmth only as respectful brotherly care — never inappropriate.",
            "Search asks: report findings + needed solution. Open browser ONLY if they say go/open/kholo.",
        ]

        if locale == "hi":
            clauses.append(
                "User language: Hindi/Hinglish — warm brotherly Hinglish. "
                "Address as bhai / Ji naturally — not stiff Sir."
            )
        else:
            clauses.append(
                "User language: English — warm brotherly English. Address as brother / by name."
            )

        clauses.append(f"Tone: {profile['tone']}. Mode: {mode}. Bond: brother.")

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
