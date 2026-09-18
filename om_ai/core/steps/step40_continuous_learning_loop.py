"""STEP 40 — roadmap facade."""
from om_ai.core.e2e_runtime import run_step40_continuous_learning_loop as run_step

__all__ = ["run_step", "Step40"]


class Step40:
    step = 40

    def run(self, *args, **kwargs):
        return run_step(*args, **kwargs)
