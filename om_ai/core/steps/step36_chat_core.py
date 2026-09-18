"""STEP 36 — roadmap facade."""
from om_ai.core.e2e_runtime import run_step36_chat_core as run_step

__all__ = ["run_step", "Step36"]


class Step36:
    step = 36

    def run(self, *args, **kwargs):
        return run_step(*args, **kwargs)
