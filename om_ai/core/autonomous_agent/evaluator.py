from __future__ import annotations
from typing import Any

class Evaluator:
    def score(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        done = sum(1 for r in results if r.get("status") in {"done", "planned", "queued"})
        return {"score": min(1.0, done / max(1, len(results))), "results": len(results)}
