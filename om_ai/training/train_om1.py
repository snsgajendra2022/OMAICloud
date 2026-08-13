"""OM-1.0 smoke / local training entry (truthful; not 70B)."""
from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import torch

from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer
from om_ai.tokenizer import load_tokenizer, tokenizer_fingerprint
from om_ai.training.trainer import Trainer, TrainingConfig, build_dataset


def _pick_device(device: str | None) -> str:
    if device:
        return device
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _default_corpus(root: Path) -> str:
    candidates = [
        root / "data/production-corpus/shards/shard-00000.jsonl",
        root / "data/production-corpus/clean/fineweb-deduped.jsonl",
        root / "data/production-corpus/clean/fineweb-1gb.jsonl",
        root / "artifacts/corpus.jsonl",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    raise FileNotFoundError(
        "No FineWeb / corpus file found. Pass --data explicitly."
    )


def _default_tokenizer(root: Path) -> str:
    for rel in (
        "artifacts/tokenizer-fixed-v3.json",
        "artifacts/tokenizer-om-production.json",
        "artifacts/demo/tokenizer.json",
    ):
        p = root / rel
        if p.is_file():
            return str(p)
    raise FileNotFoundError("No OM tokenizer found under artifacts/")


def run_train_om1(
    *,
    config: str | None = None,
    data: str | None = None,
    tokenizer: str | None = None,
    output: str | None = None,
    steps: int = 20,
    batch_size: int = 4,
    lr: float = 3e-4,
    device: str | None = None,
    max_tokens: int | None = 250_000,
    max_docs: int | None = 2000,
    checkpoint_every: int = 10,
    log_every: int = 1,
    precision: str = "auto",
    resume: str | None = None,
) -> dict:
    root = Path(__file__).resolve().parents[2]
    config = config or str(root / "configs/om-1.0-local.json")
    data = data or _default_corpus(root)
    tokenizer = tokenizer or _default_tokenizer(root)
    output = output or str(root / "artifacts/checkpoints/om-1.0-smoke")
    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = ModelConfig.from_json(config)
    tok = load_tokenizer(tokenizer)
    cfg.vocab_size = len(tok.vocab)
    tok_fp = tokenizer_fingerprint(tokenizer)
    dev = _pick_device(device)

    model = OMTransformer(cfg)
    tc = TrainingConfig(
        steps=steps,
        batch_size=batch_size,
        learning_rate=lr,
        output_dir=str(out_dir),
        checkpoint_every=checkpoint_every,
        log_every=log_every,
        precision=precision,
        warmup_steps=min(5, max(1, steps // 4)),
    )
    trainer = Trainer(model, tc, device=dev)
    if resume:
        trainer.load_checkpoint(resume)

    ds = build_dataset(
        data,
        tok,
        cfg.max_seq_len,
        max_tokens=max_tokens,
        max_docs=max_docs,
    )
    print(
        json.dumps(
            {
                "event": "om1_train_start",
                "name": "OM-1.0",
                "config": config,
                "data": data,
                "tokenizer": tokenizer,
                "tokenizer_fingerprint": tok_fp,
                "device": str(trainer.device),
                "parameters": model.exact_parameter_count(),
                "dataset_blocks": len(ds),
                "steps": steps,
                "max_tokens": max_tokens,
                "max_docs": max_docs,
                "output": str(out_dir),
                "not_70b": True,
            }
        )
    )

    result = trainer.train(ds)
    latest = out_dir / "latest.pt"
    # Re-save with tokenizer binding metadata for mismatch rejection.
    extra = {
        "tokenizer_fingerprint": tok_fp,
        "tokenizer_path": tokenizer,
        "config_path": config,
        "data_path": data,
        "model_name": "OM-1.0",
        "trained": True,
        "smoke": steps < 1000,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    trainer.save_checkpoint(latest, extra=extra)
    trainer.save_checkpoint(out_dir / f"step-{trainer.global_step}.pt", extra=extra)

    # Update registry metadata with real values only.
    reg_dir = root / "artifacts/models/om-1.0"
    reg_dir.mkdir(parents=True, exist_ok=True)
    # Optionally copy/symlink checkpoint into registry layout.
    reg_ckpt = reg_dir / "checkpoint.pt"
    if latest.is_file():
        if reg_ckpt.exists() or reg_ckpt.is_symlink():
            reg_ckpt.unlink()
        try:
            os.symlink(latest.resolve(), reg_ckpt)
        except OSError:
            import shutil

            shutil.copy2(latest, reg_ckpt)

    meta = {
        "name": "OM-1.0",
        "provider": "OM AI",
        "backend": "om_native",
        "version": "1.0",
        "lifecycle": "checkpoint_available",
        "trained": True,
        "config": config,
        "tokenizer": tokenizer,
        "tokenizer_fingerprint": tok_fp,
        "checkpoint": str(latest.resolve()),
        "parameters": model.exact_parameter_count(),
        "device": str(trainer.device),
        "steps": trainer.global_step,
        "last_loss": result.get("last_loss"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "not_70b": True,
        "model_config": asdict(cfg),
    }
    (reg_dir / "metadata.json").write_text(json.dumps(meta, indent=2) + "\n")

    payload = {
        **result,
        "checkpoint": str(latest),
        "registry_metadata": str(reg_dir / "metadata.json"),
        "tokenizer_fingerprint": tok_fp,
        "trained": True,
        "device": str(trainer.device),
        "parameters": model.exact_parameter_count(),
    }
    print(json.dumps({"event": "om1_train_done", **payload}))
    return payload
