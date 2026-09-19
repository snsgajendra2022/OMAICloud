from __future__ import annotations

class ResponseMood:
    def label(self, state: str) -> str:
        return (state or "WAITING").lower()
