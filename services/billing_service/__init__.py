"""Billing / usage metering (local ledger; provider optional)."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from services._common import ServiceHealth, ok


class BillingService:
    def __init__(self, db: str = "artifacts/enterprise/billing.jsonl") -> None:
        self.path = Path(db)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def health(self) -> dict[str, Any]:
        return ServiceHealth("billing-service", detail={"mode": "local_ledger"}).to_dict()

    def record_usage(self, *, tenant_id: str, tokens_in: int, tokens_out: int, model: str) -> dict[str, Any]:
        # simple cost model: $0.000001 per token placeholder
        cost = (tokens_in + tokens_out) * 0.000001
        row = {
            "ts": time.time(),
            "tenant_id": tenant_id,
            "model": model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": round(cost, 8),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        return ok(row)

    def summary(self, tenant_id: str = "default") -> dict[str, Any]:
        total = 0.0
        n = 0
        if self.path.is_file():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("tenant_id") == tenant_id:
                    total += float(row.get("cost_usd") or 0)
                    n += 1
        return ok({"tenant_id": tenant_id, "events": n, "cost_usd": round(total, 6)})
