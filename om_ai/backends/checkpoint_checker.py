"""OM-1.0 checkpoint verification — non-fatal for serve bootstrap."""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from om_ai.backends.om_native import default_native_paths

logger = logging.getLogger(__name__)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def verify_file(path: str | Path | None, *, min_bytes: int = 64) -> dict[str, Any]:
    """Check that a file exists and is non-trivial."""
    if not path:
        return {"ok": False, "status": "MISSING", "path": "", "reason": "path unset"}
    p = Path(path)
    if not p.is_absolute():
        p = _repo_root() / p
    if not p.is_file():
        return {"ok": False, "status": "MISSING", "path": str(p), "reason": f"Checkpoint missing: {p}"}
    size = p.stat().st_size
    if size < min_bytes:
        return {
            "ok": False,
            "status": "INVALID",
            "path": str(p),
            "reason": f"file too small ({size} bytes)",
            "size": size,
        }
    return {"ok": True, "status": "FOUND", "path": str(p), "size": size}


def validate_metadata(paths: dict[str, str] | None = None) -> dict[str, Any]:
    """Validate config + tokenizer + checkpoint trio."""
    paths = paths or default_native_paths()
    ckpt = verify_file(paths.get("checkpoint"), min_bytes=1024)
    tok = verify_file(paths.get("tokenizer"), min_bytes=64)
    cfg = verify_file(paths.get("config"), min_bytes=16)
    return {
        "checkpoint": ckpt,
        "tokenizer": tok,
        "config": cfg,
        "paths": {k: paths.get(k) for k in ("checkpoint", "tokenizer", "config", "device")},
    }


def load_test(*, require_weights: bool = False) -> dict[str, Any]:
    """Attempt a lightweight native load. Never raises for serve health."""
    try:
        from om_ai.backends.om_native import OMNativeBackend

        backend = OMNativeBackend()
        info = backend.load(require_checkpoint=True)
        return {
            "ok": bool(backend.loaded and getattr(backend, "_trained", False)),
            "status": "SUCCESS" if backend.loaded else "FAILED",
            "info": {
                "trained": info.get("trained"),
                "device": info.get("device"),
                "vocab_size": (info.get("tokenizer") or {}).get("vocab_size")
                if isinstance(info.get("tokenizer"), dict)
                else info.get("vocab_size"),
            },
        }
    except Exception as exc:
        logger.info("checkpoint load_test failed (brain-only OK): %s", exc)
        if require_weights:
            return {"ok": False, "status": "FAILED", "error": str(exc)}
        return {
            "ok": False,
            "status": "FAILED",
            "error": str(exc),
            "fallback": "brain-only",
        }


def check_checkpoint(*, try_load: bool = False) -> dict[str, Any]:
    """Full model status report for doctor / health UI."""
    meta = validate_metadata()
    ckpt = meta["checkpoint"]
    tok = meta["tokenizer"]
    cfg = meta["config"]

    out: dict[str, Any] = {
        "checkpoint": ckpt.get("status", "MISSING"),
        "tokenizer": tok.get("status", "MISSING"),
        "config": cfg.get("status", "MISSING"),
        "checkpoint_path": ckpt.get("path") or "",
        "tokenizer_path": tok.get("path") or "",
        "config_path": cfg.get("path") or "",
        "loading": "SKIPPED",
        "fallback": None,
        "env": {
            "OM_MODEL_CHECKPOINT": os.getenv("OM_MODEL_CHECKPOINT") or "",
            "OM_AI_CHECKPOINT": os.getenv("OM_AI_CHECKPOINT") or "",
            "OM_MODEL_TOKENIZER": os.getenv("OM_MODEL_TOKENIZER") or os.getenv("OM_AI_TOKENIZER") or "",
            "OM_MODEL_CONFIG": os.getenv("OM_MODEL_CONFIG") or os.getenv("OM_AI_CONFIG") or "",
        },
    }

    if not ckpt.get("ok"):
        out["loading"] = "FAILED"
        out["fallback"] = "brain-only"
        out["error"] = ckpt.get("reason") or "Checkpoint missing"
        return out

    if try_load:
        loaded = load_test(require_weights=False)
        out["loading"] = loaded.get("status", "FAILED")
        out["load"] = loaded
        if not loaded.get("ok"):
            out["fallback"] = "brain-only"
            out["error"] = loaded.get("error")
    else:
        # File present is enough for READY/FOUND; serve does real load.
        out["loading"] = "READY" if tok.get("ok") and cfg.get("ok") else "PARTIAL"

    return out


def format_model_status(report: dict[str, Any] | None = None) -> str:
    report = report or check_checkpoint(try_load=False)
    lines = [
        "Model Status:",
        "",
        f"Checkpoint:  {report.get('checkpoint')}",
        f"Tokenizer:   {report.get('tokenizer')}",
        f"Config:      {report.get('config')}",
        "",
        f"Loading:     {report.get('loading')}",
    ]
    if report.get("checkpoint_path"):
        lines.append(f"Path:        {report['checkpoint_path']}")
    if report.get("fallback"):
        lines.append(f"Fallback:    {report['fallback']}")
    if report.get("error"):
        lines.append(f"Error:       {report['error']}")
    return "\n".join(lines)
