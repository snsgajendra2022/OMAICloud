from __future__ import annotations
from typing import Any
from .companion_runtime import get_companion_runtime
from .config import CompanionConfig


def start_companion(**overrides) -> dict[str, Any]:
    cfg = CompanionConfig.from_env(**overrides)
    rt = get_companion_runtime()
    # apply overrides onto existing
    for k, v in overrides.items():
        if hasattr(rt.config, k) and v is not None:
            setattr(rt.config, k, v)
    return rt.start()


def format_banner(status: dict[str, Any]) -> str:
    lines = [
        "============================================",
        "           OM AI COMPANION RUNTIME",
        "============================================",
        "",
    ]
    for c in status.get("components") or []:
        name = str(c.get("name") or "")
        st = str(c.get("status") or "")
        lines.append(f"  {name:<22} {st}")
    lines += [
        "",
        f"  Wake phrase: {status.get('wake_phrase') or 'hey om'}",
        f"  Status: {status.get('status')}",
        "============================================",
    ]
    return "\n".join(lines)
