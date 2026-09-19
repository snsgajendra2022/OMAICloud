from __future__ import annotations

class Recovery:
    def next_on_fail(self, step_id: str) -> str:
        return f"Retry {step_id} with narrower scope, then report."
