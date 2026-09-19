"""User profile — long-term preferences and identity."""
from __future__ import annotations

import re
from typing import Any

from om_ai.core.companion_memory import get_memory_service


class UserProfile:
    def __init__(self, user_key: str = "default:user") -> None:
        self.user_key = user_key
        self._cache: dict[str, str] = {}

    def load(self) -> dict[str, Any]:
        svc = get_memory_service()
        prefs = {}
        try:
            prefs = dict(svc.preferences.get_prefs(self.user_key) or {})
        except Exception:
            prefs = {}
        name = self._cache.get("name") or prefs.get("name") or ""
        return {"user_key": self.user_key, "name": name, "preferences": prefs, **self._cache}

    def observe(self, text: str) -> dict[str, Any]:
        """Extract and persist simple facts from speech."""
        svc = get_memory_service()
        low = (text or "").strip()
        updates: dict[str, str] = {}
        m = re.search(
            r"(?:my name is|i am|i'm|mera naam|main)\s+([A-Za-z\u0900-\u097F]{2,40})",
            low,
            re.I,
        )
        if m:
            name = m.group(1).strip(" .,!")
            if name.lower() not in {"om", "jarvis", "sir", "the"}:
                updates["name"] = name
                self._cache["name"] = name
                try:
                    svc.remember_fact(self.user_key, "name", name)
                    if hasattr(svc, "set_preference"):
                        svc.set_preference(self.user_key, "name", name)
                except Exception:
                    pass
        m2 = re.search(r"(?:i (?:like|love|prefer)|mujhe|pasand)\s+(.+?)(?:\.|$)", low, re.I)
        if m2:
            fact = m2.group(1).strip(" .,!")[:120]
            if len(fact) >= 3:
                updates["preference"] = fact
                try:
                    svc.remember_fact(self.user_key, "preference", fact)
                except Exception:
                    pass
        return {"updates": updates, "profile": self.load()}
