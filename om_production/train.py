"""Core weight training pipeline for OM production chatbot (Mac MPS / CUDA / CPU)."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch

from model import OMProductionLLM
from tokenizer import OMTokenizer

HERE = Path(__file__).resolve().parent


def pick_device(preferred: str | None = None) -> torch.device:
    pref = (preferred or os.getenv("OM_DEVICE") or "").strip().lower()
    if pref:
        return torch.device(pref)
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Train OM production LLM on dataset.txt")
    p.add_argument("--dataset", default=str(HERE / "dataset.txt"))
    p.add_argument("--tokenizer", default=str(HERE / "om_tokenizer.json"))
    p.add_argument("--out", default=str(HERE / "om_chatgpt_level_weights.pt"))
    p.add_argument("--block-size", type=int, default=256)
    p.add_argument("--n-embd", type=int, default=256)
    p.add_argument("--n-head", type=int, default=8)
    p.add_argument("--n-layer", type=int, default=6)
    p.add_argument("--vocab-size", type=int, default=4000)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--steps", type=int, default=2000)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--device", default="")
    p.add_argument("--grad-clip", type=float, default=1.0)
    p.add_argument("--log-every", type=int, default=100)
    p.add_argument("--checkpoint-every", type=int, default=500)
    args = p.parse_args(argv)

    device = pick_device(args.device or None)
    print(f"Target hardware node established: {str(device).upper()}")

    tok_path = Path(args.tokenizer)
    tokenizer = OMTokenizer(vocab_size=args.vocab_size)
    if not tok_path.is_file():
        print("Tokenizer JSON missing — training tokenizer from dataset first...")
        tokenizer.train(args.dataset)
    else:
        tokenizer.load(tok_path)

    vocab_size = len(tokenizer.encoder)
    with open(args.dataset, "r", encoding="utf-8") as f:
        raw_data = f.read()
    tokenized_stream = torch.tensor(tokenizer.encode(raw_data), dtype=torch.long)
    if tokenized_stream.numel() < args.block_size + 2:
        raise SystemExit("dataset.txt too small after tokenization — add more dialogue rows")

    def get_training_batch():
        ix = torch.randint(len(tokenized_stream) - args.block_size, (args.batch_size,))
        x = torch.stack([tokenized_stream[i : i + args.block_size] for i in ix])
        y = torch.stack([tokenized_stream[i + 1 : i + args.block_size + 1] for i in ix])
        return x.to(device), y.to(device)

    model = OMProductionLLM(
        vocab_size, args.n_embd, args.n_head, args.n_layer, args.block_size
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)

    print(
        json.dumps(
            {
                "engine": "om_production.train",
                "device": str(device),
                "vocab": vocab_size,
                "params": sum(p.numel() for p in model.parameters()),
                "tokens": int(tokenized_stream.numel()),
                "steps": args.steps,
            }
        ),
        flush=True,
    )
    print("Executing Deep Weight Optimization Matrix Pipeline...")
    model.train()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    for step in range(args.steps):
        xb, yb = get_training_batch()
        _, loss = model(xb, yb)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=args.grad_clip)
        optimizer.step()
        if step % args.log_every == 0 or step == args.steps - 1:
            print(
                f"Matrix Optimization Step {step:4d} | Deep Cross-Entropy Loss: {loss.item():.4f}",
                flush=True,
            )
        if args.checkpoint_every and step > 0 and step % args.checkpoint_every == 0:
            mid = out.with_name(f"{out.stem}_step{step}{out.suffix}")
            torch.save(
                {
                    "model": model.state_dict(),
                    "meta": {
                        "vocab_size": vocab_size,
                        "n_embd": args.n_embd,
                        "n_head": args.n_head,
                        "n_layer": args.n_layer,
                        "block_size": args.block_size,
                        "tokenizer": str(tok_path),
                    },
                    "step": step,
                },
                mid,
            )

    torch.save(
        {
            "model": model.state_dict(),
            "meta": {
                "vocab_size": vocab_size,
                "n_embd": args.n_embd,
                "n_head": args.n_head,
                "n_layer": args.n_layer,
                "block_size": args.block_size,
                "tokenizer": str(tok_path if tok_path.is_file() else HERE / "om_tokenizer.json"),
            },
            "step": args.steps,
        },
        out,
    )
    print(f"Success: production model weights saved locally as '{out}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
