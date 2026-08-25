"""Track OM software/intelligence versions after improvement cycles."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


VERSION_PATH = Path("artifacts/improvement/om_versions.json")


def current_version(path: str | Path | None = None) -> dict[str, Any]:
    p = Path(path or VERSION_PATH)
    if not p.is_file():
        return {"om_version": "1.0", "improve_cycle": 0, "history": []}
    return json.loads(p.read_text(encoding="utf-8"))


def bump_version(
    *,
    note: str = "",
    metrics: dict[str, Any] | None = None,
    path: str | Path | None = None,
) -> dict[str, Any]:
    p = Path(path or VERSION_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    state = current_version(p)
    cycle = int(state.get("improve_cycle") or 0) + 1
    entry = {
        "ts": time.time(),
        "cycle": cycle,
        "note": note,
        "metrics": metrics or {},
    }
    history = list(state.get("history") or [])
    history.append(entry)
    state = {
        "om_version": "1.0",
        "improve_cycle": cycle,
        "label": f"OM-1.0-improve-{cycle}",
        "history": history[-50:],
        "updated_at": time.time(),
    }
    p.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return state
