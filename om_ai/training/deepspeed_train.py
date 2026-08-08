"""DeepSpeed ZeRO-3 entry for OMTransformer with partition-aware init."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from om_ai.core.config import ModelConfig
from om_ai.tokenizer import ByteBPETokenizer
from om_ai.training.partition_init import create_om_transformer, recommended_strategy
from om_ai.training.trainer import build_dataset


def main():
    try:
        import deepspeed
    except ImportError as exc:
        raise SystemExit("Install with: pip install -e '.[deepSpeed]'") from exc

    ap = argparse.ArgumentParser(description="OM AI DeepSpeed ZeRO-3 trainer")
    ap.add_argument("--config", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--deepspeed", required=True)
    ap.add_argument("--output", default=None)
    ap.add_argument("--local_rank", type=int, default=-1)
    ap.add_argument(
        "--partition-init",
        action="store_true",
        default=True,
        help="Build model under deepspeed.zero.Init (required for 70B-scale)",
    )
    ap.add_argument("--no-partition-init", action="store_true", help="Legacy eager full-model init (OOM risk)")
    ap.add_argument("--log-every", type=int, default=10)
    args = ap.parse_args()

    cfg = ModelConfig.from_json(args.config)
    tok = ByteBPETokenizer.load(args.tokenizer)
    cfg.vocab_size = len(tok.vocab)
    ds_cfg = json.load(open(args.deepspeed))
    out_dir = Path(
        args.output
        or os.getenv("OM_AI_TRAIN_OUTPUT", "artifacts/checkpoints/deepspeed")
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    use_partition = args.partition_init and not args.no_partition_init
    strategy = "deepspeed_zero3" if use_partition else "eager"
    if not use_partition and recommended_strategy(cfg.parameter_estimate()) != "eager":
        print(
            "WARNING: eager init on a large architecture may OOM before ZeRO partitions. "
            "Prefer --partition-init (default).",
            flush=True,
        )

    model = create_om_transformer(
        cfg,
        strategy=strategy,
        deepspeed_config=ds_cfg,
        dtype=torch.bfloat16 if ds_cfg.get("bf16", {}).get("enabled") else torch.float16,
    )
    if cfg.gradient_checkpointing:
        model.set_gradient_checkpointing(True)

    ds = build_dataset(args.data, tok, cfg.max_seq_len)
    engine, _, loader, _ = deepspeed.initialize(
        model=model,
        model_parameters=model.parameters(),
        training_data=ds,
        config=ds_cfg,
    )

    steps = int(ds_cfg.get("scheduler", {}).get("params", {}).get("total_num_steps", 1000))
    step = 0
    tokens = 0
    t0 = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
    t1 = torch.cuda.Event(enable_timing=True) if torch.cuda.is_available() else None
    if t0:
        t0.record()

    metrics_path = out_dir / "train_metrics.jsonl"
    for batch in loader:
        x, y = [z.to(engine.device) for z in batch]
        loss = engine(x, labels=y)["loss"]
        engine.backward(loss)
        engine.step()
        step += 1
        tokens += int(x.numel())
        if engine.global_rank == 0 and step % args.log_every == 0:
            row = {"step": step, "loss": float(loss), "tokens": tokens}
            print(row, flush=True)
            with metrics_path.open("a") as fh:
                fh.write(json.dumps(row) + "\n")
        if step >= steps:
            break

    if t1 and t0:
        t1.record()
        torch.cuda.synchronize()
        ms = t0.elapsed_time(t1)
        if engine.global_rank == 0:
            print({"throughput_tokens_per_sec": tokens / (ms / 1000.0) if ms else None}, flush=True)

    tag = f"step{step}"
    engine.save_checkpoint(str(out_dir), tag=tag)
    if engine.global_rank == 0:
        # Marker for the launcher (full consolidated export is cluster-specific)
        (out_dir / "LATEST_TAG.txt").write_text(tag)
        print(json.dumps({"checkpoint_dir": str(out_dir), "tag": tag, "steps": step}), flush=True)


if __name__ == "__main__":
    main()
