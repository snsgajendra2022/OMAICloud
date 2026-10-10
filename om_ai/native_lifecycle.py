"""Auditable native-OM lifecycle commands.

Run with: python -m om_ai.native_lifecycle {info|validate|train|evaluate}
This module uses OM's existing ModelConfig, OMTransformer, tokenizer and Trainer.
It never downloads or silently substitutes a third-party model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import time
from pathlib import Path
from typing import Any

import torch

from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer
from om_ai.tokenizer import load_tokenizer
from om_ai.training import Trainer, TrainingConfig, build_dataset
from om_ai.training.production_pipeline import pick_training_device

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(path: str | Path) -> ModelConfig:
    cfg = ModelConfig.from_json(path)
    # Fail early on dimensions that would otherwise fail deep in attention.
    if cfg.d_model % cfg.n_heads:
        raise ValueError("d_model must be divisible by n_heads")
    if not cfg.n_kv_heads or cfg.n_heads % cfg.n_kv_heads:
        raise ValueError("n_heads must be divisible by n_kv_heads")
    if cfg.max_seq_len < 2:
        raise ValueError("max_seq_len must be at least 2")
    return cfg


def model_info(config_path: str, tokenizer_path: str | None = None) -> dict[str, Any]:
    cfg = load_config(config_path)
    payload: dict[str, Any] = {
        "model_family": "native_om",
        "config": str(config_path),
        "architecture": "decoder-only Transformer / RoPE / GQA / SwiGLU",
        "parameters_estimated": cfg.parameter_estimate(),
        "parameters_estimated_millions": round(cfg.parameter_estimate() / 1e6, 3),
        "layers": cfg.n_layers,
        "hidden_size": cfg.d_model,
        "query_heads": cfg.n_heads,
        "key_value_heads": cfg.n_kv_heads,
        "feed_forward_size": cfg.d_ff,
        "context_length": cfg.max_seq_len,
        "vocab_size": cfg.vocab_size,
        "gradient_checkpointing": cfg.gradient_checkpointing,
        "weights_available": False,
        "production_ready": False,
        "note": "Architecture metadata is not evidence of trained capability.",
    }
    if tokenizer_path:
        tok = load_tokenizer(tokenizer_path)
        cfg.vocab_size = len(tok.vocab)
        model = OMTransformer(cfg)
        payload.update({
            "tokenizer": str(tokenizer_path),
            "tokenizer_sha256": sha256_file(tokenizer_path),
            "tokenizer_vocab_size": len(tok.vocab),
            "parameters_exact": model.exact_parameter_count(),
            "trainable_parameters": model.trainable_parameter_count(),
        })
    return payload


def validate(config_path: str, device: str | None = None, output: str = "artifacts/validation") -> dict[str, Any]:
    """Exercise real forward/backward and checkpoint round-trip on a tiny sequence."""
    cfg = load_config(config_path)
    # Keep validation bounded regardless of the production context preset.
    cfg.max_seq_len = min(cfg.max_seq_len, 32)
    cfg.vocab_size = min(max(cfg.vocab_size, 64), 512)
    model = OMTransformer(cfg)
    dev = torch.device(device or pick_training_device())
    model.to(dev).train()
    x = torch.randint(0, cfg.vocab_size, (2, min(8, cfg.max_seq_len)), device=dev)
    y = torch.randint(0, cfg.vocab_size, x.shape, device=dev)
    result = model(x)
    logits = result.get("logits") if isinstance(result, dict) else (result[0] if isinstance(result, (tuple, list)) else result)
    if logits is None or logits.shape[:2] != x.shape:
        raise RuntimeError(f"Unexpected model output shape: {getattr(logits, 'shape', None)}")
    loss = torch.nn.functional.cross_entropy(logits.reshape(-1, cfg.vocab_size), y.reshape(-1))
    if not torch.isfinite(loss):
        raise RuntimeError("Forward pass produced non-finite loss")
    loss.backward()
    grad_count = sum(p.grad is not None and torch.isfinite(p.grad).all().item() for p in model.parameters())
    if grad_count == 0:
        raise RuntimeError("Backward pass produced no finite gradients")
    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = out_dir / "native-validation-roundtrip.pt"
    torch.save({"model": model.state_dict(), "model_config": cfg.to_dict()}, checkpoint)
    restored = OMTransformer(cfg).to(dev)
    saved = torch.load(checkpoint, map_location=dev, weights_only=True)
    restored.load_state_dict(saved["model"], strict=True)
    restored.eval()
    with torch.no_grad():
        check = restored(x)
        check_logits = check.get("logits") if isinstance(check, dict) else (check[0] if isinstance(check, (tuple, list)) else check)
    if not torch.allclose(logits.detach(), check_logits, atol=1e-4, rtol=1e-4):
        raise RuntimeError("Checkpoint round-trip changed model outputs")
    return {
        "status": "passed",
        "device": str(dev),
        "parameters_exact": model.exact_parameter_count(),
        "loss": float(loss.detach().cpu()),
        "finite_gradient_tensors": int(grad_count),
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256_file(checkpoint),
        "production_ready": False,
        "note": "Architecture smoke test passed; this does not certify generation quality.",
    }


def train(args: argparse.Namespace) -> dict[str, Any]:
    cfg = load_config(args.config)
    tok = load_tokenizer(args.tokenizer)
    cfg.vocab_size = len(tok.vocab)
    model = OMTransformer(cfg)
    device = args.device or pick_training_device()
    tc = TrainingConfig(
        steps=args.steps, batch_size=args.batch_size,
        grad_accum_steps=args.grad_accum, learning_rate=args.lr,
        checkpoint_every=args.checkpoint_every, log_every=args.log_every,
        precision=args.precision, output_dir=args.output,
        seed=args.seed, min_free_gb=args.min_free_gb,
    )
    trainer = Trainer(model, tc, device=device)
    if args.resume:
        trainer.load_checkpoint(args.resume)
    dataset = build_dataset(args.data, tok, cfg.max_seq_len)
    if len(dataset) < 1:
        raise ValueError("Training dataset produced zero token blocks.")
    started = time.time()
    metrics = trainer.train(dataset)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    latest = out / "latest.pt"
    trainer.save_checkpoint(latest, extra={
        "model_family": "native_om",
        "config_path": str(args.config),
        "tokenizer_path": str(args.tokenizer),
        "tokenizer_sha256": sha256_file(args.tokenizer),
        "dataset_path": str(args.data),
        "dataset_sha256": sha256_file(args.data),
        "run_started_unix": started,
        "run_finished_unix": time.time(),
        "device": str(trainer.device),
        "license_review_required": True,
    })
    manifest = {
        "model_family": "native_om",
        "config": str(args.config), "config_sha256": sha256_file(args.config),
        "tokenizer": str(args.tokenizer), "tokenizer_sha256": sha256_file(args.tokenizer),
        "dataset": str(args.data), "dataset_sha256": sha256_file(args.data),
        "checkpoint": str(latest), "checkpoint_sha256": sha256_file(latest),
        "global_step": trainer.global_step, "parameters": model.exact_parameter_count(),
        "device": str(trainer.device), "metrics": metrics,
        "trained_weights": True, "quality_evaluated": False, "production_ready": False,
    }
    manifest_path = out / "run-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Native OM training lifecycle")
    sub = parser.add_subparsers(dest="command", required=True)
    p_info = sub.add_parser("info", help="Report architecture and exact count when tokenizer is supplied")
    p_info.add_argument("--config", required=True)
    p_info.add_argument("--tokenizer")
    p_val = sub.add_parser("validate", help="Run forward/backward/checkpoint smoke test")
    p_val.add_argument("--config", required=True)
    p_val.add_argument("--device")
    p_val.add_argument("--output", default="artifacts/validation")
    p_train = sub.add_parser("train", help="Pretrain native OM using the repository trainer")
    p_train.add_argument("--config", required=True)
    p_train.add_argument("--tokenizer", required=True)
    p_train.add_argument("--data", required=True)
    p_train.add_argument("--output", required=True)
    p_train.add_argument("--steps", type=int, default=100)
    p_train.add_argument("--batch-size", type=int, default=1)
    p_train.add_argument("--grad-accum", type=int, default=1)
    p_train.add_argument("--lr", type=float, default=3e-4)
    p_train.add_argument("--checkpoint-every", type=int, default=25)
    p_train.add_argument("--log-every", type=int, default=5)
    p_train.add_argument("--precision", choices=("auto", "fp32", "fp16", "bf16"), default="auto")
    p_train.add_argument("--device")
    p_train.add_argument("--resume")
    p_train.add_argument("--seed", type=int, default=42)
    p_train.add_argument("--min-free-gb", type=float, default=1.0)
    args = parser.parse_args()
    if args.command == "info":
        payload = model_info(args.config, args.tokenizer)
    elif args.command == "validate":
        payload = validate(args.config, args.device, args.output)
    else:
        if args.steps < 1 or args.batch_size < 1 or args.grad_accum < 1:
            parser.error("steps, batch-size, and grad-accum must be positive")
        for required in (args.config, args.tokenizer, args.data):
            if not Path(required).is_file():
                parser.error(f"Required input file not found: {required}")
        payload = train(args)
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
