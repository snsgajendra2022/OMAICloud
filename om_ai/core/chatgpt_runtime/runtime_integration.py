"""STEP 30 helpers — wire controller into chat/API paths."""
from __future__ import annotations

import os
from typing import Any

from .om_brain_controller import OMBrainController, run_om_brain_controller


def chatgpt_runtime_enabled() -> bool:
    return (os.getenv("OM_CHATGPT_RUNTIME") or "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def run_chatgpt_runtime(message: str, **kwargs: Any) -> dict[str, Any]:
    if not chatgpt_runtime_enabled():
        return {
            "answer": "",
            "handled": False,
            "meta": {"step": 30, "disabled": True},
            "stages": ["chatgpt_runtime_disabled"],
        }
    pack = run_om_brain_controller(message, **kwargs)
    pack["handled"] = bool(str(pack.get("answer") or "").strip())
    return pack


__all__ = [
    "OMBrainController",
    "run_om_brain_controller",
    "run_chatgpt_runtime",
    "chatgpt_runtime_enabled",
]
