"""User preference tracking for OM Chat Intelligence."""
from __future__ import annotations

from typing import Any


class UserPreference:
    """Infer and store lightweight per-user chat preferences."""

    def __init__(self) -> None:
        self._prefs: dict[str, dict[str, Any]] = {}

    def get(self, user_key: str) -> dict[str, Any]:
        return dict(self._prefs.get(user_key) or {
            "tone": "friendly",
            "detail": "balanced",
            "code_style": "practical",
        })

    def update_from_message(self, user_key: str, message: str) -> dict[str, Any]:
        prefs = self.get(user_key)
        low = (message or "").lower()
        if any(w in low for w in ("brief", "short", "tl;dr", "concise")):
            prefs["detail"] = "short"
        elif any(w in low for w in ("detailed", "in depth", "thorough", "explain fully")):
            prefs["detail"] = "detailed"
        if any(w in low for w in ("formal", "professional")):
            prefs["tone"] = "professional"
        elif any(w in low for w in ("casual", "friendly", "simple")):
            prefs["tone"] = "friendly"
        if any(w in low for w in ("code only", "just code", "snippet")):
            prefs["code_style"] = "code_first"
        self._prefs[user_key] = prefs
        return prefs

    def set(self, user_key: str, **kwargs: Any) -> dict[str, Any]:
        prefs = self.get(user_key)
        prefs.update({k: v for k, v in kwargs.items() if v is not None})
        self._prefs[user_key] = prefs
        return prefs
