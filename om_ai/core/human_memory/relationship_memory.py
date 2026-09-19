from __future__ import annotations
import json
from pathlib import Path
from typing import Any

class RelationshipMemory:
    def __init__(self) -> None:
        self.path = Path("artifacts/companion/human_memory/relationship.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"trust": 0.6, "address_as": "Sir", "notes": []}

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def note(self, text: str) -> None:
        notes = list(self.data.get("notes") or [])
        notes.append(text[:300])
        self.data["notes"] = notes[-40:]
        self.save()

    def to_dict(self) -> dict[str, Any]:
        return dict(self.data)
