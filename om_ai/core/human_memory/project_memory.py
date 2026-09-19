from __future__ import annotations
import json
from pathlib import Path
from typing import Any

class ProjectMemory:
    def __init__(self) -> None:
        self.path = Path("artifacts/companion/human_memory/projects.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"active": "OM", "projects": {"OM": {"last_focus": "companion_voice"}}}

    def save(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def set_focus(self, project: str, focus: str) -> None:
        projects = self.data.setdefault("projects", {})
        projects[project] = {"last_focus": focus}
        self.data["active"] = project
        self.save()

    def to_dict(self) -> dict[str, Any]:
        return dict(self.data)
