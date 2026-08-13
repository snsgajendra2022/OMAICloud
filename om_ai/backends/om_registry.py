"""OM-1.0 model registry under ``artifacts/models/om-1.0/`` (truthful metadata only)."""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from om_ai.tokenizer import tokenizer_fingerprint, tokenizer_sha256


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def registry_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "artifacts" / "models" / "om-1.0"


def pick_best_checkpoint(root: Path | None = None) -> Path | None:
    """Prefer ``om-1.0-long/latest.pt`` if valid, else smoke, else registry symlink."""
    root = root or repo_root()
    candidates = [
        root / "artifacts" / "checkpoints" / "om-1.0-long" / "latest.pt",
        root / "artifacts" / "checkpoints" / "om-1.0-smoke" / "latest.pt",
        root / "artifacts" / "models" / "om-1.0" / "checkpoint.pt",
    ]
    for c in candidates:
        if c.is_file() and _checkpoint_loadable(c):
            return c.resolve()
    return None


def _checkpoint_loadable(path: Path) -> bool:
    try:
        ck = torch.load(path, map_location="cpu", weights_only=False)
        if not isinstance(ck, dict):
            return False
        return "model" in ck or any(isinstance(k, str) for k in ck)
    except Exception:
        return False


def stamp_tokenizer_binding(
    checkpoint: Path,
    tokenizer_path: str | Path,
    *,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    """Ensure checkpoint ``extra`` includes tokenizer_sha256 / fingerprint (atomic)."""
    tok_path = str(tokenizer_path)
    fp = tokenizer_sha256(tok_path)
    ck = torch.load(checkpoint, map_location="cpu", weights_only=False)
    if not isinstance(ck, dict):
        raise ValueError(f"Unexpected checkpoint format: {checkpoint}")
    extra = dict(ck.get("extra") or {})
    extra["tokenizer_fingerprint"] = fp
    extra["tokenizer_sha256"] = fp
    extra["tokenizer_path"] = tok_path
    if config_path:
        extra["config_path"] = str(config_path)
    extra["model_name"] = "OM-1.0"
    extra["trained"] = True
    ck["extra"] = extra

    p = Path(checkpoint)
    tmp = p.with_name(f".{p.name}.{os.getpid()}.tmp")
    torch.save(ck, tmp)
    os.replace(tmp, p)
    return extra


def sync_om10_registry(
    *,
    checkpoint: str | Path | None = None,
    tokenizer: str | Path | None = None,
    config: str | Path | None = None,
    root: Path | None = None,
    stamp_checkpoint: bool = True,
) -> dict[str, Any]:
    """Write real metadata + symlink from the best available OM checkpoint."""
    root = root or repo_root()
    reg = registry_dir(root)
    reg.mkdir(parents=True, exist_ok=True)

    ckpt = Path(checkpoint) if checkpoint else pick_best_checkpoint(root)
    if ckpt is None or not Path(ckpt).is_file():
        meta = {
            "name": "OM-1.0",
            "provider": "OM AI",
            "backend": "om_native",
            "version": "1.0",
            "lifecycle": "architecture_created",
            "trained": False,
            "error": "OM-1.0 checkpoint unavailable.",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "not_70b": True,
        }
        (reg / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
        return meta

    ckpt = Path(ckpt).resolve()
    tok = Path(
        tokenizer
        or os.getenv("OM_MODEL_TOKENIZER")
        or os.getenv("OM_AI_TOKENIZER")
        or root / "artifacts" / "tokenizer-fixed-v3.json"
    )
    cfg = Path(
        config
        or os.getenv("OM_MODEL_CONFIG")
        or os.getenv("OM_AI_CONFIG")
        or root / "configs" / "om-1.0-local.json"
    )

    extra: dict[str, Any] = {}
    if stamp_checkpoint and tok.is_file():
        extra = stamp_tokenizer_binding(ckpt, tok, config_path=cfg if cfg.is_file() else None)

    ck_blob = torch.load(ckpt, map_location="cpu", weights_only=False)
    global_step = int(ck_blob.get("global_step") or 0) if isinstance(ck_blob, dict) else 0
    model_config = ck_blob.get("model_config") if isinstance(ck_blob, dict) else None
    parameters = None
    # Prefer exact count via architecture + tokenizer (avoid double-counting tied weights).
    try:
        from om_ai.core.config import ModelConfig
        from om_ai.model import OMTransformer
        from om_ai.tokenizer import load_tokenizer

        if cfg.is_file() and tok.is_file():
            mcfg = ModelConfig.from_json(cfg)
            mcfg.vocab_size = len(load_tokenizer(tok).vocab)
            parameters = OMTransformer(mcfg).exact_parameter_count()
    except Exception:
        parameters = None

    tok_fp = tokenizer_fingerprint(tok) if tok.is_file() else extra.get("tokenizer_sha256")

    reg_ckpt = reg / "checkpoint.pt"
    if reg_ckpt.exists() or reg_ckpt.is_symlink():
        reg_ckpt.unlink()
    try:
        os.symlink(ckpt, reg_ckpt)
    except OSError:
        shutil.copy2(ckpt, reg_ckpt)

    meta = {
        "name": "OM-1.0",
        "provider": "OM AI",
        "backend": "om_native",
        "version": "1.0",
        "lifecycle": "checkpoint_available",
        "trained": True,
        "config": str(cfg),
        "tokenizer": str(tok),
        "tokenizer_fingerprint": tok_fp,
        "tokenizer_sha256": tok_fp,
        "checkpoint": str(ckpt),
        "parameters": parameters,
        "steps": global_step,
        "model_config": model_config,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "not_70b": True,
        "honesty": "Local OM-1.0 checkpoint; not production frontier intelligence.",
    }
    (reg / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def load_registry_metadata(root: Path | None = None) -> dict[str, Any] | None:
    path = registry_dir(root) / "metadata.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None
