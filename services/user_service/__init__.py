"""User management service."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from services._common import ServiceHealth, ok


class UserService:
    def __init__(self, db: str = "artifacts/enterprise/users.json") -> None:
        self.path = Path(db)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.is_file():
            self.path.write_text("{}", encoding="utf-8")

    def health(self) -> dict[str, Any]:
        return ServiceHealth("user-service").to_dict()

    def _load(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8") or "{}")

    def _save(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def create(self, email: str, *, role: str = "viewer", org: str = "default") -> dict[str, Any]:
        data = self._load()
        uid = str(uuid.uuid4())
        data[uid] = {"id": uid, "email": email, "role": role, "org": org, "created_at": time.time()}
        self._save(data)
        return ok(data[uid])

    def list_users(self) -> dict[str, Any]:
        return ok(list(self._load().values()))
