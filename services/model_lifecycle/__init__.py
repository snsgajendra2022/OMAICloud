"""Model lifecycle — registry, experiment, deploy candidacy."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from services._common import ServiceHealth, ok


class ModelLifecycleService:
    def __init__(self, path: str = "artifacts/enterprise/model_lifecycle.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.is_file():
            self.path.write_text(
                json.dumps(
                    {
                        "models": {
                            "om-1.0": {"state": "production", "checkpoint": "local"},
                            "om-1b": {"state": "config_ready"},
                            "om-7b": {"state": "config_ready"},
                            "om-70b": {"state": "config_ready"},
                        },
                        "experiments": [],
                        "deployments": [],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

    def health(self) -> dict[str, Any]:
        return ServiceHealth("model-lifecycle").to_dict()

    def _load(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def register_experiment(self, name: str, metrics: dict[str, Any]) -> dict[str, Any]:
        data = self._load()
        exp = {"name": name, "metrics": metrics, "ts": time.time()}
        data.setdefault("experiments", []).append(exp)
        self._save(data)
        return ok(exp)

    def promote(self, model_id: str, state: str = "candidate") -> dict[str, Any]:
        data = self._load()
        models = data.setdefault("models", {})
        models[model_id] = {**(models.get(model_id) or {}), "state": state, "updated_at": time.time()}
        data.setdefault("deployments", []).append({"model_id": model_id, "state": state, "ts": time.time()})
        self._save(data)
        return ok(models[model_id])

    def status(self) -> dict[str, Any]:
        return ok(self._load())
