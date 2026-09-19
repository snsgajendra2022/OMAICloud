from __future__ import annotations
from typing import Any

class MultilingualContext:
    def __init__(self) -> None:
        self.preferred_reply_mix = "auto"  # auto | en | hi-en

    def reply_locale(self, detected: dict[str, Any]) -> str:
        mix = detected.get("mix") or "en"
        if mix in {"hi", "hi-en"}:
            return "hi"
        return "en"
