"""STEP 30 — Final ChatGPT-like Runtime Integration."""
from om_ai.core.chatgpt_runtime import OMBrainController, run_om_brain_controller, run_chatgpt_runtime

__all__ = [
    "OMBrainController",
    "run_om_brain_controller",
    "run_chatgpt_runtime",
    "Step30ChatGPTRuntime",
]


class Step30ChatGPTRuntime(OMBrainController):
    step = 30
