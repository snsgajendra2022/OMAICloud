from __future__ import annotations
from typing import Any
from .companion_runtime import get_companion_runtime, reset_companion_runtime


def stop_companion() -> dict[str, Any]:
    rt = get_companion_runtime()
    out = rt.stop()
    reset_companion_runtime()
    return out
