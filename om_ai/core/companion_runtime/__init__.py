"""STEP 50 — OM Companion Runtime."""
from .config import CompanionConfig
from .companion_runtime import CompanionRuntime, get_companion_runtime, reset_companion_runtime
from .startup import start_companion, format_banner
from .shutdown import stop_companion

__all__ = [
    "CompanionConfig",
    "CompanionRuntime",
    "get_companion_runtime",
    "reset_companion_runtime",
    "start_companion",
    "format_banner",
    "stop_companion",
]
