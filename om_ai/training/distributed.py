"""DDP / FSDP distributed training with optional meta-device partition-aware init."""
from __future__ import annotations

import argparse
import os
from dataclasses import asdict
from pathlib import Path

import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, DistributedSampler

from om_ai.core.config import ModelConfig
from om_ai.tokenizer import load_tokenizer
from om_ai.training.partition_init import create_om_transformer, wrap_fsdp
from om_ai.training.trainer import build_dataset


def main():
    ap = argparse.ArgumentParser(description="OM AI DDP/FSDP trainer")
    ap.add_argument("--config", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--strategy", choices=["ddp", "fsdp"], default="ddp")
    ap.add_argument("--steps", type=int, default=1000)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--output", default="artifacts/checkpoints")
    ap.add_argument(
        "--partition-init",
        action="store_true",
        help="For FSDP: build on meta device then materialize under FSDP (large models)",
    )
    args = ap.parse_args()

    dist.init_process_group(backend="nccl" if torch.cuda.is_available() else "gloo")
    rank = dist.get_rank()
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    if torch.cuda.is_available():
        torch.cuda.set_device(local_rank)
    device = torch.device(f"cuda:{local_rank}" if torch.cuda.is_available() else "cpu")

    cfg = ModelConfig.from_json(args.config)
    tok = load_tokenizer(args.tokenizer)
    cfg.vocab_size = len(tok.vocab)

    if args.strategy == "fsdp" and args.partition_init:
        model = create_om_transformer(cfg, strategy="meta")
        if cfg.gradient_checkpointing:
            model.set_gradient_checkpointing(True)
        model = wrap_fsdp(model, local_rank=local_rank, use_meta=True)
    else:
        model = create_om_transformer(cfg, strategy="eager").to(device)
        if cfg.gradient_checkpointing:
            model.set_gradient_checkpointing(True)
        if args.strategy == "ddp":
            model = DDP(
                model,
                device_ids=[local_rank] if device.type == "cuda" else None,
            )
        else:
            model = wrap_fsdp(model, local_rank=local_rank, use_meta=False)

    ds = build_dataset(args.data, tok, cfg.max_seq_len)
    sampler = DistributedSampler(ds, shuffle=True)
    dl = DataLoader(ds, batch_size=args.batch_size, sampler=sampler)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    step = 0
    while step < args.steps:
        sampler.set_epoch(step)
        for x, y in dl:
            x, y = x.to(device), y.to(device)
            out = model(x, labels=y)
            out["loss"].backward()
            opt.step()
            opt.zero_grad(set_to_none=True)
            step += 1
            if rank == 0 and step % 10 == 0:
                print({"step": step, "loss": float(out["loss"])}, flush=True)
            if step >= args.steps:
                break
    if rank == 0:
        Path(args.output).mkdir(parents=True, exist_ok=True)
        raw = model.module if hasattr(model, "module") else model
        torch.save(
            {"model": raw.state_dict(), "model_config": asdict(cfg)},
            Path(args.output) / "distributed-latest.pt",
        )
    dist.destroy_process_group()


if __name__ == "__main__":
    main()
