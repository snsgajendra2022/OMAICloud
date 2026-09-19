from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any

class PreferenceMemory:
    def __init__(self) -> None:
        self.path = Path("artifacts/companion/human_memory/preferences.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"detail": "balanced", "tone": "jarvis", "language": "auto"}

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def observe(self, text: str) -> dict[str, Any]:
        low = (text or "").lower()
        changed = False
        if re.search(r"(?i)detailed|in detail|technical answers|detail mein", low):
            self.data["detail"] = "detailed"; changed = True
        if re.search(r"(?i)short|brief|short answers|short mein", low):
            self.data["detail"] = "concise"; changed = True
        if re.search(r"(?i)call me sir|address me as sir", low):
            self.data["address_as"] = "Sir"; changed = True
        if changed:
            self.save()
        return dict(self.data)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.data)
