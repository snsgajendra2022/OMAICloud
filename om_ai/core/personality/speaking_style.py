from __future__ import annotations
import re

class SpeakingStyle:
    def polish(self, text: str, *, address: str = "Sir") -> str:
        t = (text or "").strip()
        if not t:
            return t
        # Avoid FAQ openers
        t = re.sub(r"(?i)^hello[,!]?\s*i am om[,.]?\s*what can i (do|help).*", "", t).strip() or t
        if "sir" not in t.lower() and address and len(t.split()) < 28:
            if t.endswith("?"):
                return t
            if not t.endswith((".", "!", "…")):
                t += "."
        return t
