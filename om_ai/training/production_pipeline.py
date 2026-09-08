"""3-stage ChatGPT production pipeline for OM-1.0 on Mac (MPS).

Stage 1 — Pre-Training (base next-token LM on raw/clean corpus)
Stage 2 — SFT (assistant-only causal loss on chat JSONL)
Stage 3 — DPO (prefer good completions over gibberish)

This module inventories local data, picks MPS when available, and can launch
the existing ``om-ai train|sft|dpo`` entrypoints with the right checkpoints.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


@dataclass(slots=True)
class DatasetStat:
    path: str
    exists: bool
    size_bytes: int = 0
    size_human: str = "0B"
    rows: int | None = None
    role: str = ""


@dataclass(slots=True)
class PipelineInventory:
    device: str
    mps_available: bool
    cuda_available: bool
    total_data_bytes: int
    total_data_human: str
    approx_pretrain_tokens: int
    approx_pretrain_tokens_human: str
    chat_sft_rows: int
    chat_dpo_rows: int
    bottleneck: str
    datasets: list[DatasetStat] = field(default_factory=list)
    checkpoints: dict[str, str] = field(default_factory=dict)
    architecture: dict[str, bool] = field(default_factory=dict)
    recommended_next: list[str] = field(default_factory=list)


def _human_bytes(n: int) -> str:
    x = float(max(0, n))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if x < 1024.0 or unit == "TB":
            return f"{x:.1f}{unit}" if unit != "B" else f"{int(x)}B"
        x /= 1024.0
    return f"{n}B"


def _human_tokens(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def pick_training_device(preferred: str | None = None) -> str:
    """Prefer MPS on Apple Silicon for OM training (ChatGPT-path on Mac)."""
    import torch

    env = (preferred or os.getenv("OM_DEVICE") or os.getenv("OM_TRAIN_DEVICE") or "").strip()
    if env:
        return env
    # On Darwin, prefer Metal over CUDA stubs / CPU.
    if platform.system() == "Darwin" and torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _count_jsonl_rows(path: Path, limit: int = 5_000_000) -> int | None:
    if not path.is_file():
        return None
    if path.suffix not in {".jsonl", ".json"} and "jsonl" not in path.name:
        return None
    # Skip multi-GB files for row counting — estimate from size instead
    if path.stat().st_size > 200_000_000:
        return None
    n = 0
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.strip():
                n += 1
                if n >= limit:
                    break
    return n


def _stat(path: Path, role: str) -> DatasetStat:
    exists = path.exists()
    size = path.stat().st_size if path.is_file() else (
        sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) if path.is_dir() else 0
    )
    rows = _count_jsonl_rows(path) if path.is_file() else None
    return DatasetStat(
        path=str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path),
        exists=exists,
        size_bytes=size,
        size_human=_human_bytes(size),
        rows=rows,
        role=role,
    )


def inventory(root: Path | None = None) -> PipelineInventory:
    """Measure local corpora vs ChatGPT-scale requirements (honest gap report)."""
    import torch

    root = root or ROOT
    tracked = [
        (root / "data" / "production-corpus" / "clean" / "fineweb-1gb.jsonl", "pretrain"),
        (root / "data" / "production-corpus" / "clean" / "fineweb-deduped.jsonl", "pretrain"),
        (root / "data" / "om-knowledge-brain-v1" / "train" / "om_knowledge_instruct_v1.jsonl", "instruct"),
        (root / "data" / "om-chat-sft-v4-complete.jsonl", "sft"),
        (root / "data" / "om-chat-sft-v3-human.jsonl", "sft"),
        (root / "data" / "om-chat-dpo-v4.jsonl", "dpo"),
        (root / "data" / "sft" / "chat_conversations.example.jsonl", "sft_example"),
        (root / "data" / "dpo" / "preferences.example.jsonl", "dpo_example"),
    ]
    datasets = [_stat(p, role) for p, role in tracked]
    data_root = root / "data"
    total = (
        sum(p.stat().st_size for p in data_root.rglob("*") if p.is_file())
        if data_root.is_dir()
        else 0
    )

    # ~4 chars/token rough estimate for English web text
    pretrain_bytes = sum(d.size_bytes for d in datasets if d.role == "pretrain" and d.exists)
    approx_tokens = int(pretrain_bytes / 4)

    sft_rows = sum(d.rows or 0 for d in datasets if d.role == "sft" and d.rows)
    dpo_rows = sum(d.rows or 0 for d in datasets if d.role == "dpo" and d.rows)

    if sft_rows < 50_000:
        bottleneck = (
            f"Chat SFT scale is the bottleneck: ~{sft_rows} conversational rows "
            f"(ChatGPT-class needs 100k–millions). Pretrain corpus locally is "
            f"~{_human_bytes(pretrain_bytes)} (~{_human_tokens(approx_tokens)} est. tokens), "
            "not trillion-token OpenAI scale."
        )
    elif approx_tokens < 10_000_000_000:
        bottleneck = (
            f"Pretrain scale is limited (~{_human_tokens(approx_tokens)} est. tokens). "
            "Continue expanding clean web/code corpora, then re-run SFT/DPO."
        )
    else:
        bottleneck = "Data scale looks strong for a local OM; focus on longer SFT/DPO runs and eval."

    ckpt_map = {
        "base": "artifacts/checkpoints/om-1.0-base/latest.pt",
        "sft": "artifacts/checkpoints/om-1.0-chat-sft-v4/latest.pt",
        "sft_alt": "artifacts/checkpoints/om-1.0-chat-sft/latest.pt",
        "dpo": "artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt",
        "long": "artifacts/checkpoints/om-1.0-long/latest.pt",
    }
    checkpoints = {
        k: v for k, v in ckpt_map.items() if (root / v).is_file()
    }

    from om_ai.training.chatgpt_upgrade import audit_chatgpt_parity

    audit = audit_chatgpt_parity().as_dict()
    device = pick_training_device()
    rec = [
        f"# Device for this Mac run: {device}",
        "# Scratch-to-train (educational / quick MPS smoke):",
        f".venv/bin/python train_om.py --mode toy --max-iters 500 --device {device}",
        "# Production pretrain (owned OMTransformer + local tokenizer):",
        (
            f".venv/bin/python train_om.py --mode production --max-iters 2000 "
            f"--data data/production-corpus/clean/fineweb-deduped.jsonl --device {device}"
        ),
        (
            "om-ai sft --config configs/om-1.0-local.json "
            "--tokenizer artifacts/tokenizer-production-65536.json "
            "--data data/om-chat-sft-v4-complete.jsonl "
            "--checkpoint artifacts/checkpoints/om-1.0-base/latest.pt "
            f"--output artifacts/checkpoints/om-1.0-chat-sft-v4 --device {device}"
        ),
        (
            "om-ai dpo --config configs/om-1.0-local.json "
            "--tokenizer artifacts/tokenizer-production-65536.json "
            "--data data/om-chat-dpo-v4.jsonl "
            "--checkpoint artifacts/checkpoints/om-1.0-chat-sft-v4/latest.pt "
            f"--output artifacts/checkpoints/om-1.0-chat-dpo-v4 --device {device} --beta 0.1"
        ),
        "export OM_MODEL_CHECKPOINT=artifacts/checkpoints/om-1.0-chat-dpo-v4/latest.pt",
        "om-ai serve",
    ]

    return PipelineInventory(
        device=device,
        mps_available=bool(torch.backends.mps.is_available()),
        cuda_available=bool(torch.cuda.is_available()),
        total_data_bytes=total,
        total_data_human=_human_bytes(total),
        approx_pretrain_tokens=approx_tokens,
        approx_pretrain_tokens_human=_human_tokens(approx_tokens),
        chat_sft_rows=sft_rows,
        chat_dpo_rows=dpo_rows,
        bottleneck=bottleneck,
        datasets=datasets,
        checkpoints=checkpoints,
        architecture={
            "rope": bool(audit.get("rope")),
            "rmsnorm": bool(audit.get("rmsnorm")),
            "swiglu": bool(audit.get("swiglu")),
            "sdpa": bool(audit.get("scaled_dot_product_attention")),
            "om_causal_loss": True,
            "assistant_only_sft_labels": True,
        },
        recommended_next=rec,
    )


def inventory_dict(root: Path | None = None) -> dict[str, Any]:
    inv = inventory(root)
    d = asdict(inv)
    return d


def run_stage(
    stage: str,
    *,
    device: str | None = None,
    dry_run: bool = True,
    steps: int | None = None,
) -> dict[str, Any]:
    """Launch one pipeline stage via the ``om-ai`` CLI (MPS-aware)."""
    inv = inventory()
    device = device or inv.device
    root = ROOT
    py = sys.executable
    om_ai = str(root / ".venv" / "bin" / "om-ai")
    if not Path(om_ai).is_file():
        om_ai = "om-ai"

    config = "configs/om-1.0-local.json"
    tokenizer = "artifacts/tokenizer-production-65536.json"
    if not (root / tokenizer).is_file():
        tokenizer = "artifacts/tokenizer-fixed-v3.json"
    stage = stage.strip().lower()

    if stage in {"pretrain", "train", "1"}:
        data = "data/production-corpus/clean/fineweb-deduped.jsonl"
        if not (root / data).is_file():
            data = "data/production-corpus/clean/fineweb-1gb.jsonl"
        cmd = [
            om_ai,
            "train",
            "--config",
            config,
            "--tokenizer",
            tokenizer,
            "--data",
            data,
            "--output",
            "artifacts/checkpoints/om-1.0-base",
            "--device",
            device,
        ]
        if steps:
            cmd.extend(["--steps", str(steps)])
    elif stage in {"sft", "2"}:
        ckpt = inv.checkpoints.get("base") or inv.checkpoints.get("long")
        if not ckpt:
            raise FileNotFoundError("No base checkpoint found for SFT")
        cmd = [
            om_ai,
            "sft",
            "--config",
            config,
            "--tokenizer",
            tokenizer,
            "--data",
            "data/om-chat-sft-v4-complete.jsonl",
            "--checkpoint",
            ckpt,
            "--output",
            "artifacts/checkpoints/om-1.0-chat-sft-v4",
            "--device",
            device,
        ]
        if steps:
            cmd.extend(["--steps", str(steps)])
    elif stage in {"dpo", "3"}:
        ckpt = inv.checkpoints.get("sft") or inv.checkpoints.get("sft_alt")
        if not ckpt:
            raise FileNotFoundError("No SFT checkpoint found for DPO")
        cmd = [
            om_ai,
            "dpo",
            "--config",
            config,
            "--tokenizer",
            tokenizer,
            "--data",
            "data/om-chat-dpo-v4.jsonl",
            "--checkpoint",
            ckpt,
            "--output",
            "artifacts/checkpoints/om-1.0-chat-dpo-v4",
            "--device",
            device,
            "--beta",
            "0.1",
        ]
        if steps:
            cmd.extend(["--steps", str(steps)])
    else:
        raise ValueError(f"Unknown stage {stage!r}; use pretrain|sft|dpo")

    payload = {"stage": stage, "device": device, "cmd": cmd, "dry_run": dry_run}
    if dry_run:
        return payload
    proc = subprocess.run(cmd, cwd=str(root), check=False)
    payload["returncode"] = proc.returncode
    return payload
