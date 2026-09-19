from __future__ import annotations
from typing import Any

class Worker:
    def run(self, node: dict[str, Any], *, execute: bool = False) -> dict[str, Any]:
        return {"id": node.get("id"), "status": "done" if execute else "queued", "label": node.get("label")}
