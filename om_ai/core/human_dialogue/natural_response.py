from __future__ import annotations
import re

class NaturalResponse:
    """Natural companion lines — never robotic FAQ."""

    def for_intent(self, intent: str, *, address: str = "Sir", locale: str = "en") -> str | None:
        hi = locale == "hi"
        table = {
            "bad_day": (
                f"Main sun raha hoon, {address}. Bura din raha — kya hua, bataiye?"
                if hi
                else f"I am sorry to hear that, {address}. Do you want to talk about what happened?"
            ),
            "fatigue": (
                f"Lamba din, {address}? Thoda break lijiye. Kya hua?"
                if hi
                else f"Long day, {address}? Take a breath. What happened?"
            ),
            "problem": (
                f"Samajh gaya, {address}. Main sun raha hoon — clearly boliye."
                if hi
                else f"I hear you, {address}. Tell me what happened — I am listening."
            ),
            "greeting": (
                f"Good morning, {address}. Hazir hoon."
                if hi
                else f"Good morning, {address}. I am ready."
            ),
            "thanks": (
                f"Hamesha, {address}."
                if hi
                else f"Always, {address}."
            ),
        }
        return table.get(intent)

    def detect(self, text: str) -> str:
        low = (text or "").lower()
        if re.search(r"(?i)bad\s*day|bura\s*din|horrible day|rough day", low):
            return "bad_day"
        if re.search(r"(?i)\b(tired|exhausted|thak)\b", low):
            return "fatigue"
        if re.search(r"(?i)\b(problem|stuck|error|bug)\b", low):
            return "problem"
        if re.search(r"(?i)good morning|subah|hello|hey om", low):
            return "greeting"
        if re.search(r"(?i)thank|shukriya", low):
            return "thanks"
        return "general"
