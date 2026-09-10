"""Detect corrupted / meaningless model output and nonsense user asks."""
from __future__ import annotations

import re


class GarbageDetector:

    _RANDOM_REQUEST = re.compile(
        r"\b("
        r"generate\s+random\s+words?"
        r"|random\s+(?:gibberish|nonsense|garbage|text|string)"
        r"|output\s+meaningless"
        r"|spew\s+random"
        r"|corrupted\s+content"
        r")\b",
        re.I,
    )

    _REFUSAL = (
        "I can help generate text, but I will not output "
        "meaningless corrupted content."
    )

    def is_nonsense_request(self, message: str) -> bool:
        text = (message or "").strip()
        if not text:
            return False
        return bool(self._RANDOM_REQUEST.search(text))

    def refusal_message(self) -> str:
        return self._REFUSAL

    def check(self, text: str) -> bool:
        """Return True when text looks like garbage / corrupted output."""
        if not text:
            return False

        words = text.split()
        if not words:
            return True

        # High unique-token density → word salad
        if len(words) > 40:
            unique = len({w.lower() for w in words})
            if unique / len(words) > 0.85:
                return True

        # Repeated stutter / loop
        low = text.lower()
        if re.search(r"\b(\w+)(?:\s+\1){4,}\b", low):
            return True

        # Replacement chars / tokenizer junk
        if text.count("�") >= 2:
            return True

        # Weird casing soup
        weird = 0
        for word in words:
            if len(word) > 28:
                weird += 1
                continue
            up = sum(1 for c in word if c.isupper())
            lo = sum(1 for c in word if c.islower())
            if up >= 3 and lo >= 3 and not word.isupper():
                weird += 1
        if len(words) >= 12 and weird / len(words) > 0.2:
            return True

        # Fragment soup: many commas, no sentence end
        if (
            len(words) >= 12
            and text.count(",") >= 5
            and text.count(".") == 0
            and "http" not in low
        ):
            return True

        return False
