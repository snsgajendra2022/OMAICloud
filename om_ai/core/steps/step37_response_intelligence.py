"""STEP 37 — roadmap facade."""
from om_ai.core.e2e_runtime import run_step37_response_intelligence as run_step

__all__ = ["run_step", "Step37"]


class Step37:
    step = 37

    def run(self, *args, **kwargs):
        return run_step(*args, **kwargs)
