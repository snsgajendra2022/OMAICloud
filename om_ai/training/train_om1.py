"""OM-1.0 smoke / local training entry (truthful; not 70B)."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import torch

from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer
from om_ai.tokenizer import load_tokenizer, tokenizer_fingerprint
from om_ai.training.trainer import Trainer, TrainingConfig, build_dataset

# Apple Silicon / CPU sanity: looping 70e12 steps on 100MB FineWeb cannot
# produce ChatGPT-class English and will never finish.
_MAC_MAX_STEPS = 250_000
_MAC_MAX_TOKENS = 2_000_000
_MAC_MAX_DOCS = 25_000


def _clamp_mac_train(
    *,
    steps: int,
    max_tokens: int | None,
    max_docs: int | None,
    device: str,
    allow_unbounded: bool,
) -> tuple[int, int | None, int | None, dict]:
    note: dict = {}
    cuda = device == "cuda" or (device or "").startswith("cuda")
    if cuda or allow_unbounded:
        return steps, max_tokens, max_docs, note
    if steps > _MAC_MAX_STEPS:
        note["steps_clamped_from"] = steps
        steps = _MAC_MAX_STEPS
    if max_tokens is not None and max_tokens > _MAC_MAX_TOKENS:
        note["max_tokens_clamped_from"] = max_tokens
        max_tokens = _MAC_MAX_TOKENS
    if max_docs is not None and max_docs > _MAC_MAX_DOCS:
        note["max_docs_clamped_from"] = max_docs
        max_docs = _MAC_MAX_DOCS
    if note:
        note["reason"] = (
            "OM-1.0-local is ~20M params / 128 context on this Mac. "
            "Unbounded steps do not become ChatGPT. Pass --allow-unbounded-steps to override."
        )
    return steps, max_tokens, max_docs, note


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
    allow_unbounded: bool = False,
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
    steps, max_tokens, max_docs, clamp_note = _clamp_mac_train(
        steps=steps,
        max_tokens=max_tokens,
        max_docs=max_docs,
        device=dev,
        allow_unbounded=allow_unbounded,
    )

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
        try:
            trainer.load_checkpoint(resume)
        except ValueError as e:
            if "Corrupt checkpoint" not in str(e):
                raise
            # Auto-fallback so a stale/partial latest.pt does not abort training.
            print(
                json.dumps(
                    {
                        "event": "om1_resume_corrupt",
                        "path": resume,
                        "warning": str(e),
                        "fallback": "from_scratch",
                    }
                ),
                flush=True,
            )
            trainer.global_step = 0

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
                "not_chatgpt": True,
                "clamp": clamp_note or None,
            }
        ),
        flush=True,
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

    from om_ai.backends.om_registry import sync_om10_registry

    meta = sync_om10_registry(
        checkpoint=latest,
        tokenizer=tokenizer,
        config=config,
        root=root,
        stamp_checkpoint=True,
    )
    # Preserve training-run metrics that sync may not know.
    meta["device"] = str(trainer.device)
    meta["parameters"] = model.exact_parameter_count()
    meta["steps"] = trainer.global_step
    meta["last_loss"] = result.get("last_loss")
    meta["model_config"] = asdict(cfg)
    meta["tokenizer_fingerprint"] = tok_fp
    meta["tokenizer_sha256"] = tok_fp
    reg_dir = root / "artifacts/models/om-1.0"
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
    print(json.dumps({"event": "om1_train_done", **payload}), flush=True)
    return payload
