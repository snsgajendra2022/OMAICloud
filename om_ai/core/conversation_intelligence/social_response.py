"""Social layer — no canned greeting bank. Brain owns spoken replies."""
from __future__ import annotations


class SocialResponseEngine:
    def respond(self, intent: str | None) -> str:
        del intent
        return ""
