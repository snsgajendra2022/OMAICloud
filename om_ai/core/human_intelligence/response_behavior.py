"""Response behavior — how OM should reply after meaning is known."""
from __future__ import annotations

from typing import Any


class ResponseBehavior:
    """Maps meaning → concrete reply behavior (before SolutionEngine)."""

    def decide(
        self,
        *,
        meaning: dict[str, Any] | None = None,
        intent: dict[str, Any] | None = None,
        feeling: dict[str, Any] | None = None,
        emotion: str = "neutral",
        route: dict[str, Any] | None = None,
        locale: str = "en",
    ) -> dict[str, Any]:
        meaning = meaning or {}
        intent = intent or {}
        feeling = feeling or {}
        route = route or {}
        mode = str(route.get("mode") or "answer")
        hi = locale == "hi"

        if mode == "listen" or meaning.get("needs_listening"):
            seed = meaning.get("natural_ask") or (
                "Aaj din bhari laga. Kya hua?"
                if hi
                else "It sounds like today was really heavy for you. What happened?"
            )
            if emotion in {"disappointed"} or "fail" in str(meaning.get("text") or "").lower():
                seed = (
                    "Yeh sunke disappointment feel hoti hai. Kya galat gaya — baat karni hai?"
                    if hi
                    else "That sounds disappointing. Do you want to talk about what went wrong?"
                )
            return {
                "style": "supportive",
                "move": "acknowledge_then_ask",
                "seed_reply": seed,
                "followup": seed,
                "max_sentences": 2,
                "solve": False,
            }

        if mode == "search":
            return {
                "style": "informative",
                "move": "search_summarize",
                "seed_reply": (
                    "Main dhoondhta hun aur jo mila woh bataata hun — browser nahi kholunga jab tak tum bolo."
                    if hi
                    else "I'll research that and summarize what I find — I won't open anything unless you say so."
                ),
                "followup": (
                    "Koi source kholna ho to bolo."
                    if hi
                    else "Want me to open any source?"
                ),
                "max_sentences": 4,
                "solve": False,
            }

        if mode == "action":
            return {
                "style": "careful",
                "move": "ask_permission",
                "seed_reply": (
                    "Main yeh kar sakta hun. Permission chahiye — proceed?"
                    if hi
                    else "I can do that. Permission required — proceed?"
                ),
                "followup": None,
                "max_sentences": 2,
                "solve": False,
            }

        if mode == "joke":
            return {
                "style": "light",
                "move": "humor",
                "seed_reply": (
                    "Haha theek hai — ek light wali?"
                    if hi
                    else "Ha — want a light one, or should we stay on what you were saying?"
                ),
                "max_sentences": 2,
                "solve": False,
            }

        if mode == "share":
            return {
                "style": "warm_share",
                "move": "match_energy",
                "seed_reply": (
                    "Mazaa aa gaya sunke. Aur batao?"
                    if hi
                    else "That's really good to hear. Tell me more?"
                ),
                "max_sentences": 2,
                "solve": False,
            }

        return {
            "style": feeling.get("response") or "balanced",
            "move": "answer",
            "seed_reply": "",
            "followup": None,
            "max_sentences": 3,
            "solve": intent.get("intent") in {"problem", "question"},
        }
