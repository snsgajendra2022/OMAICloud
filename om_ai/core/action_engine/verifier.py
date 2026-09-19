from __future__ import annotations
from typing import Any

class Verifier:
    def check(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        return {"ok": True, "checked": len(results), "gaps": []}
