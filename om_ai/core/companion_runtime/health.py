from __future__ import annotations
from typing import Any


def component_health(name: str, ready: bool, detail: str = "") -> dict[str, Any]:
    return {"name": name, "status": "READY" if ready else "WARN", "detail": detail, "ready": ready}
