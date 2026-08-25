"""Checkpoint path helpers."""
from __future__ import annotations

from pathlib import Path


def latest_checkpoint(run_dir: str | Path) -> Path:
    p = Path(run_dir) / "latest.pt"
    if not p.is_file():
        raise FileNotFoundError(f"No latest.pt under {run_dir}")
    return p


def list_checkpoints(run_dir: str | Path) -> list[Path]:
    root = Path(run_dir)
    return sorted(root.glob("*.pt")) + sorted(root.glob("checkpoint-*"))
