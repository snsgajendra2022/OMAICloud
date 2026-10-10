"""Canonical Production Checkpoint Loader for OM AI.

PHASE 4 - CHECKPOINT SYSTEM:
Create a canonical checkpoint loader:
ProductionCheckpointLoader

Responsibilities:
- resolve checkpoint (separate development, experiment, evaluation, production)
- validate checkpoint existence & readability
- load checkpoint safely
- validate architecture and dimensions
- validate tokenizer compatibility
- report checkpoint metadata
- fail safely with precise diagnostics
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

import torch

logger = logging.getLogger(__name__)


class CheckpointLoadError(RuntimeError):
    """Raised when checkpoint resolution, validation, or loading fails."""
    pass


@dataclass(slots=True)
class CheckpointMetadata:
    path: str
    stage: str = "production"
    vocab_size: int = 65536
    embed_dim: int = 256
    num_layers: int = 4
    num_heads: int = 4
    architecture: str = "OMTransformer"
    sha256: str = ""
    extra: dict[str, Any] = field(default_factory=dict)
    is_production_ready: bool = False


class ProductionCheckpointLoader:
    """Canonical loader for production checkpoints."""

    STAGES = {"production", "development", "experiment", "evaluation"}

    @classmethod
    def resolve_checkpoint(
        cls,
        path: str | Path | None = None,
        *,
        stage: str = "production",
        root: Path | None = None,
    ) -> Path:
        base = root or Path(".")
        if path is not None:
            p = base / path if not Path(path).is_absolute() else Path(path)
            if not p.is_file():
                raise CheckpointLoadError(f"Requested checkpoint does not exist: {p}")
            return p.resolve()

        # Canonical production paths in priority order
        if stage == "production":
            candidates = [
                base / "artifacts" / "models" / "om-1.0" / "checkpoint.pt",
                base / "artifacts" / "checkpoints" / "om-1.0-chat-dpo-v4" / "latest.pt",
                base / "artifacts" / "checkpoints" / "om-1.0-chat-sft-v4" / "latest.pt",
            ]
        elif stage == "development":
            candidates = [
                base / "artifacts" / "checkpoints" / "om-1.0-smoke" / "latest.pt",
                base / "artifacts" / "checkpoints" / "om-1.0-sft-smoke" / "latest.pt",
            ]
        else:
            candidates = [
                base / "artifacts" / "checkpoints" / "om-1.0-long" / "latest.pt",
            ]

        for cand in candidates:
            if cand.is_file():
                return cand.resolve()

        raise CheckpointLoadError(f"No valid checkpoint found for stage: {stage}")

    @classmethod
    def inspect(cls, checkpoint_path: str | Path) -> CheckpointMetadata:
        p = Path(checkpoint_path)
        if not p.is_file():
            raise CheckpointLoadError(f"Checkpoint not found: {p}")

        try:
            data = torch.load(p, map_location="cpu", weights_only=False)
        except Exception as exc:
            raise CheckpointLoadError(f"Failed to read checkpoint {p}: {exc}") from exc

        if not isinstance(data, dict):
            raise CheckpointLoadError(f"Invalid checkpoint format in {p}")

        state = data.get("model_state_dict", data.get("model", data.get("state_dict", data)))
        if not isinstance(state, dict):
            raise CheckpointLoadError(f"No valid state_dict in checkpoint {p}")

        embed_weight = state.get("token_embedding.weight")
        vocab_size = embed_weight.shape[0] if embed_weight is not None else 0
        embed_dim = embed_weight.shape[1] if embed_weight is not None else 0

        # Count layers
        layer_indices = set()
        for k in state.keys():
            if k.startswith("blocks."):
                parts = k.split(".")
                if len(parts) > 1 and parts[1].isdigit():
                    layer_indices.add(int(parts[1]))
        num_layers = len(layer_indices) if layer_indices else 4

        extra = dict(data.get("extra") or {})
        stage_tag = str(data.get("stage") or "production")

        is_ready = bool(vocab_size == 65536 and embed_dim == 256)

        return CheckpointMetadata(
            path=str(p),
            stage=stage_tag,
            vocab_size=vocab_size,
            embed_dim=embed_dim,
            num_layers=num_layers,
            num_heads=4,
            architecture="OMTransformer",
            extra=extra,
            is_production_ready=is_ready,
        )

    @classmethod
    def load(
        cls,
        checkpoint_path: str | Path | None = None,
        *,
        stage: str = "production",
        expected_vocab: int = 65536,
        root: Path | None = None,
    ) -> tuple[dict[str, Any], CheckpointMetadata]:
        resolved = cls.resolve_checkpoint(checkpoint_path, stage=stage, root=root)
        meta = cls.inspect(resolved)

        if expected_vocab > 0 and meta.vocab_size != expected_vocab:
            raise CheckpointLoadError(
                f"Checkpoint {resolved} vocab ({meta.vocab_size}) does not match expected ({expected_vocab})! "
                "Refusing to silently load incompatible weights."
            )

        sd = torch.load(resolved, map_location="cpu", weights_only=False)
        state = sd.get("model_state_dict", sd.get("model", sd.get("state_dict", sd)))
        return state, meta
