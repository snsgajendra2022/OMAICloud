"""STEP 29 — Improvement loop."""
from __future__ import annotations

from typing import Any


class ImprovementLoop:
    def run(
        self,
        *,
        failures: list[dict[str, Any]] | None = None,
        gaps: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        failures = list(failures or [])
        gaps = list(gaps or [])
        dataset = []
        for f in failures[:20]:
            dataset.append(
                {
                    "input": f.get("message") or "",
                    "bad_output_signal": f.get("issues") or [],
                    "target_skill": f.get("gap") or "conversation",
                }
            )
        for g in gaps[:10]:
            for ex in g.get("examples") or []:
                dataset.append({"input": ex, "target_skill": g.get("gap"), "source": "gap"})
        return {
            "dataset_size": len(dataset),
            "dataset": dataset[:50],
            "action": "train" if dataset else "noop",
            "flow": "bad_answer→gap→dataset→train→improve",
        }
