from __future__ import annotations
from typing import Any

class Verifier:
    def check(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        ok = all(r.get("ok") for r in results) if results else False
        return {"ok": ok, "completed": len(results), "failed": sum(1 for r in results if not r.get("ok"))}
