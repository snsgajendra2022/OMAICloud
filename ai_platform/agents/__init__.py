"""Load agent capability manifests."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def list_capabilities(root: str | Path | None = None) -> list[dict[str, Any]]:
    base = Path(root or Path(__file__).resolve().parent)
    out: list[dict[str, Any]] = []
    for path in sorted(base.glob("*/capability.json")):
        out.append(json.loads(path.read_text(encoding="utf-8")))
    return out
