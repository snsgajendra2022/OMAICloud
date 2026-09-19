from __future__ import annotations
import re
from typing import Any

class ConversationFlow:
    """Map human situations → natural Jarvis replies (not FAQ)."""

    def intent(self, text: str) -> str:
        low = (text or "").lower()
        raw = text or ""
        # Fatigue before affection — "thak gaya" / "yaad dilana" must not collide.
        if (
            re.search(r"(?i)\b(tired|exhausted|thak(?:a|i|e|o)?|thakan)\b", low)
            or "थक" in raw
            or "thak gaya" in low
            or "thak gayi" in low
            or "main thak" in low
        ):
            return "fatigue"
        if re.search(r"(?i)\b(problem|issue|stuck|error|bug|परेशान)\b", low):
            return "problem"
        if re.search(r"(?i)\b(lonely|alone|bored)\b", low):
            return "lonely"
        if re.search(r"(?i)\b(good morning|subah|सुबह)\b", low):
            return "morning"
        if re.search(r"(?i)\b(good night|raat|शुभ रात्रि)\b", low):
            return "night"
        # Affection: "miss you" / "yaad aa" — never "yaad dilana" (reminder)
        if re.search(r"(?i)\b(miss you|i miss|yaad\s*aa|miss\s+kar)\b", low) and not re.search(
            r"(?i)yaad\s*dila", low
        ):
            return "affection"
        if re.search(r"(?i)\b(what.*(doing|up)|kya kar|क्या कर)\b", low):
            return "check_in"
        if re.search(r"(?i)\b(thank|shukriya|धन्यवाद)\b", low):
            return "thanks"
        return "general"

    def human_reply(self, text: str, *, locale: str = "en", address: str = "Sir") -> str | None:
        intent = self.intent(text)
        hi = locale == "hi"
        if intent == "fatigue":
            return (
                f"Lamba din raha, {address}? Thoda break lijiye. Kya hua — bataiye."
                if hi
                else f"Long day, {address}? Take a breath. What happened?"
            )
        if intent == "problem":
            return (
                f"Samajh gaya, {address}. Main sun raha hoon — kya problem hai, clearly boliye."
                if hi
                else f"I hear you, {address}. Tell me what happened — I'm listening."
            )
        if intent == "lonely":
            return (
                f"Main yahin hoon, {address}. Akele mat feel kijiye — baat karni hai?"
                if hi
                else f"I'm right here, {address}. You don't have to carry it alone — want to talk?"
            )
        if intent == "morning":
            return (
                f"Good morning, {address}. Hazir hoon. Aaj kahan se shuru karein?"
                if hi
                else f"Good morning, {address}. Systems ready. Where shall we begin?"
            )
        if intent == "night":
            return (
                f"Good night, {address}. Aaram kijiye — main yahin rahunga."
                if hi
                else f"Good night, {address}. Rest well — I'll be here."
            )
        if intent == "affection":
            return (
                f"Main bhi, {address}. Kabhi bhi boliye — main sun raha hoon."
                if hi
                else f"Always, {address}. Speak anytime — I'm listening."
            )
        if intent == "check_in":
            return (
                f"Aapke saath hoon, {address} — sun raha hoon. Boliye, kya baat hai?"
                if hi
                else f"Standing by with you, {address}. What do you need?"
            )
        if intent == "thanks":
            return (
                f"Hamesha, {address}. Aur kuch?"
                if hi
                else f"Always, {address}. Anything else?"
            )
        return None
