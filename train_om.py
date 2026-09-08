#!/usr/bin/env python3
"""train_om.py — Scratch-to-training for OM-1.0 on Mac (MPS), fully local.

No ChatGPT / Hugging Face APIs. Weights, data, and code stay on disk.

Modes
-----
1. **bpe** (recommended scratch): self-contained sub-word BPE + ``knowledge.txt``
   chat format (``<|user|>`` / ``<|assistant|>``) for logic + emotional replies.
2. **toy**: character-level educational baseline.
3. **production**: real OMTransformer (RoPE + RMSNorm + SwiGLU + SDPA) + local Byte-BPE.

Examples
--------
  # Build knowledge.txt from local offline docs, then train BPE on MPS
  .venv/bin/python train_om.py --build-knowledge docs data/om-foundation-corpus
  .venv/bin/python train_om.py --mode bpe --data knowledge.txt --max-iters 2000

  # Production pretrain
  .venv/bin/python train_om.py --mode production --max-iters 2000 \\
      --data data/production-corpus/clean/fineweb-deduped.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from om_ai.training.local_knowledge import SEED_KNOWLEDGE, aggregate_local_docs
from om_ai.training.om_tokenizer import OMTokenizer


# =====================================================================
# 1. HARDWARE SYSTEM CHECK (MAC GPU DETECTOR)
# =====================================================================
def pick_device(preferred: str | None = None) -> torch.device:
    pref = (preferred or os.getenv("OM_DEVICE") or "").strip().lower()
    if pref:
        return torch.device(pref)
    if torch.backends.mps.is_available():
        print("SUCCESS: Training OM-1.0 natively on Apple Silicon GPU (MPS)")
        return torch.device("mps")
    if torch.cuda.is_available():
        print("SUCCESS: Training OM-1.0 on CUDA")
        return torch.device("cuda")
    print("WARNING: MPS/CUDA not found. Training on CPU.")
    return torch.device("cpu")


# =====================================================================
# 2. LOCAL DATASET LOADER (disk → tokens, memory-aware)
# =====================================================================
def ensure_knowledge_file(file_path: Path) -> Path:
    file_path = Path(file_path)
    if not file_path.is_absolute():
        file_path = ROOT / file_path
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(SEED_KNOWLEDGE, encoding="utf-8")
        print(f"Created template knowledge file → {file_path}")
    return file_path


def load_raw_text(file_path: Path, *, max_chars: int | None = None) -> str:
    """Stream-read text/jsonl from disk without requiring the whole file in RAM twice."""
    file_path = Path(file_path)
    if not file_path.is_file():
        raise FileNotFoundError(file_path)
    size = file_path.stat().st_size
    # Soft warning for multi-GB files — still stream by line for jsonl
    if size > 500_000_000:
        print(f"NOTE: Large corpus ({size / 1e9:.2f} GB). Encoding may take a while.")

    if file_path.suffix == ".jsonl" or "jsonl" in file_path.name:
        parts: list[str] = []
        total = 0
        with file_path.open("r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    chunk = line
                else:
                    if isinstance(obj, dict):
                        chunk = str(
                            obj.get("text")
                            or obj.get("content")
                            or obj.get("response")
                            or obj.get("prompt")
                            or ""
                        )
                    else:
                        chunk = str(obj)
                if not chunk:
                    continue
                parts.append(chunk)
                total += len(chunk)
                if max_chars and total >= max_chars:
                    break
        return "\n".join(parts)

    with file_path.open("r", encoding="utf-8", errors="ignore") as fh:
        if max_chars:
            return fh.read(max_chars)
        return fh.read()


def load_dataset_from_file(
    file_path: str | Path,
    tokenizer: OMTokenizer | None = None,
    *,
    vocab_size: int = 5000,
    train_sample_chars: int = 2_000_000,
    max_chars: int | None = None,
) -> tuple[torch.Tensor, OMTokenizer]:
    """Load local text, train/attach BPE vocab, return token id tensor."""
    path = ensure_knowledge_file(Path(file_path))
    raw_text = load_raw_text(path, max_chars=max_chars)
    if not raw_text.strip():
        raw_text = SEED_KNOWLEDGE

    tok = tokenizer or OMTokenizer(vocab_size=vocab_size)
    if not tok.encoder:
        # Train BPE on a sample so huge files don't explode merge time
        sample = raw_text if len(raw_text) <= train_sample_chars else raw_text[:train_sample_chars]
        tok.train_tokenizer(sample)
    numerical_tokens = tok.encode(raw_text)
    if len(numerical_tokens) < 32:
        # Ensure enough tokens for block training
        numerical_tokens = tok.encode(raw_text * 50)
    return torch.tensor(numerical_tokens, dtype=torch.long), tok


# =====================================================================
# 3. MODEL BLOCKS (RMSNorm + SwiGLU + SDPA) — shared by toy/bpe
# =====================================================================
class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-5):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        rms = x.pow(2).mean(-1, keepdim=True).add(self.eps).rsqrt()
        return self.weight * x * rms


class SwiGLU(nn.Module):
    def __init__(self, n_embd: int):
        super().__init__()
        hidden = 4 * n_embd
        self.w1 = nn.Linear(n_embd, hidden, bias=False)
        self.w2 = nn.Linear(n_embd, hidden, bias=False)
        self.proj = nn.Linear(hidden, n_embd, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.proj(F.silu(self.w1(x)) * self.w2(x))


class ToyCausalSelfAttention(nn.Module):
    def __init__(self, n_embd: int, n_head: int, block_size: int):
        super().__init__()
        assert n_embd % n_head == 0
        self.n_head = n_head
        self.head_size = n_embd // n_head
        self.key = nn.Linear(n_embd, n_embd, bias=False)
        self.query = nn.Linear(n_embd, n_embd, bias=False)
        self.value = nn.Linear(n_embd, n_embd, bias=False)
        self.proj = nn.Linear(n_embd, n_embd)
        self.register_buffer("tril", torch.tril(torch.ones(block_size, block_size)))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, t, c = x.shape
        q = self.query(x).view(b, t, self.n_head, self.head_size).transpose(1, 2)
        k = self.key(x).view(b, t, self.n_head, self.head_size).transpose(1, 2)
        v = self.value(x).view(b, t, self.n_head, self.head_size).transpose(1, 2)
        try:
            out = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        except Exception:
            wei = q @ k.transpose(-2, -1) * (self.head_size**-0.5)
            wei = wei.masked_fill(self.tril[:t, :t] == 0, float("-inf"))
            wei = F.softmax(wei, dim=-1)
            out = wei @ v
        out = out.transpose(1, 2).contiguous().view(b, t, c)
        return self.proj(out)


class ToyBlock(nn.Module):
    def __init__(self, n_embd: int, n_head: int, block_size: int):
        super().__init__()
        self.sa = ToyCausalSelfAttention(n_embd, n_head, block_size)
        self.ffwd = SwiGLU(n_embd)
        self.ln1 = RMSNorm(n_embd)
        self.ln2 = RMSNorm(n_embd)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.sa(self.ln1(x))
        x = x + self.ffwd(self.ln2(x))
        return x


class OM1ScratchModel(nn.Module):
    """Scratch OM-1.0 core for char or BPE token ids."""

    def __init__(
        self,
        vocab_size: int,
        n_embd: int,
        n_head: int,
        n_layer: int,
        block_size: int,
    ):
        super().__init__()
        self.block_size = block_size
        self.token_embedding_table = nn.Embedding(vocab_size, n_embd)
        self.position_embedding_table = nn.Embedding(block_size, n_embd)
        self.blocks = nn.Sequential(
            *[ToyBlock(n_embd, n_head, block_size) for _ in range(n_layer)]
        )
        self.ln_f = RMSNorm(n_embd)
        self.lm_head = nn.Linear(n_embd, vocab_size)

    def forward(self, idx: torch.Tensor, targets: torch.Tensor | None = None):
        _b, t = idx.shape
        device = idx.device
        tok_emb = self.token_embedding_table(idx)
        pos_emb = self.position_embedding_table(torch.arange(t, device=device))
        x = self.blocks(tok_emb + pos_emb)
        logits = self.lm_head(self.ln_f(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx: torch.Tensor, max_new_tokens: int) -> torch.Tensor:
        self.eval()
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size :]
            logits, _ = self(idx_cond)
            probs = F.softmax(logits[:, -1, :], dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, next_token), dim=1)
        return idx


# Keep alias for older references
OM1ToyModel = OM1ScratchModel


def _run_token_train_loop(
    *,
    mode: str,
    device: torch.device,
    data: torch.Tensor,
    decode_fn,
    vocab_size: int,
    args: argparse.Namespace,
    extra_save: dict | None = None,
) -> dict:
    if data.numel() < args.block_size + 2:
        raise ValueError("Corpus too small for block_size; add more text to knowledge.txt / --data")

    n = int(0.9 * len(data))
    train_data, val_data = data[:n], data[n:]

    def get_batch(split: str):
        cur = train_data if split == "train" else val_data
        hi = max(1, len(cur) - args.block_size)
        ix = torch.randint(hi, (args.batch_size,))
        x = torch.stack([cur[i : i + args.block_size] for i in ix])
        y = torch.stack([cur[i + 1 : i + args.block_size + 1] for i in ix])
        return x.to(device), y.to(device)

    model = OM1ScratchModel(
        vocab_size=vocab_size,
        n_embd=args.n_embd,
        n_head=args.n_head,
        n_layer=args.n_layer,
        block_size=args.block_size,
    ).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    n_params = sum(p.numel() for p in model.parameters())
    print(
        json.dumps(
            {
                "mode": mode,
                "device": str(device),
                "vocab_size": vocab_size,
                "params": n_params,
                "tokens": int(data.numel()),
                "max_iters": args.max_iters,
            }
        ),
        flush=True,
    )

    model.train()
    last_loss = 0.0
    for step in range(args.max_iters):
        xb, yb = get_batch("train")
        _, loss = model(xb, yb)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        last_loss = float(loss.item())
        if step % args.eval_interval == 0 or step == args.max_iters - 1:
            print(f"Step {step:4d} | loss {last_loss:.4f}", flush=True)

    out = Path(args.output)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": model.state_dict(),
        "mode": mode,
        "config": {
            "n_embd": args.n_embd,
            "n_head": args.n_head,
            "n_layer": args.n_layer,
            "block_size": args.block_size,
            "vocab_size": vocab_size,
        },
        "final_loss": last_loss,
    }
    if extra_save:
        payload.update(extra_save)
    torch.save(payload, out)
    print(f"Saved weights → {out}")

    # Start generation from <|user|> if available in extras
    start_id = 0
    if extra_save and "tokenizer_user_id" in extra_save:
        start_id = int(extra_save["tokenizer_user_id"])
    context = torch.tensor([[start_id]], dtype=torch.long, device=device)
    sample = decode_fn(model.generate(context, max_new_tokens=args.sample_tokens)[0].tolist())
    print("\n--- LIVE INFERENCE SAMPLE ---")
    print(sample)
    return {"checkpoint": str(out), "final_loss": last_loss, "sample": sample[:500]}


def run_bpe(args: argparse.Namespace) -> dict:
    """Sub-word BPE + knowledge.txt chat formatting (feelings + logic)."""
    device = pick_device(args.device or None)
    data_path = args.data or str(ROOT / "knowledge.txt")
    data, tok = load_dataset_from_file(
        data_path,
        vocab_size=int(args.vocab_size),
        train_sample_chars=int(args.train_sample_chars),
        max_chars=int(args.max_chars) if args.max_chars else None,
    )
    tok_path = Path(args.output).with_suffix(".tokenizer.json")
    if not tok_path.is_absolute():
        tok_path = ROOT / tok_path
    tok.save(tok_path)
    print(f"Saved BPE tokenizer → {tok_path}")

    return _run_token_train_loop(
        mode="bpe",
        device=device,
        data=data,
        decode_fn=tok.decode,
        vocab_size=len(tok.encoder),
        args=args,
        extra_save={
            "tokenizer_path": str(tok_path),
            "tokenizer_user_id": tok.user_id,
            "tokenizer_eos_id": tok.eos_id,
            "data_path": str(data_path),
        },
    )


def run_toy(args: argparse.Namespace) -> dict:
    """Character-level educational baseline."""
    device = pick_device(args.device or None)
    path = Path(args.data) if args.data else ensure_knowledge_file(ROOT / "knowledge.txt")
    text = load_raw_text(path) if path.is_file() else SEED_KNOWLEDGE * 50
    chars = sorted(set(text))
    stoi = {ch: i for i, ch in enumerate(chars)}
    itos = {i: ch for i, ch in enumerate(chars)}
    ids = [stoi[c] for c in text if c in stoi]
    data = torch.tensor(ids, dtype=torch.long)
    return _run_token_train_loop(
        mode="toy",
        device=device,
        data=data,
        decode_fn=lambda seq: "".join(itos.get(i, "") for i in seq),
        vocab_size=len(chars),
        args=args,
        extra_save={"vocab": chars},
    )


# =====================================================================
# 4. PRODUCTION MODE — real OM-1.0 stack
# =====================================================================
def run_production(args: argparse.Namespace) -> dict:
    from om_ai.core.config import ModelConfig
    from om_ai.model import OMTransformer
    from om_ai.tokenizer import load_tokenizer
    from om_ai.training.production_pipeline import pick_training_device
    from om_ai.training.trainer import Trainer, TrainingConfig, build_dataset

    device = args.device or pick_training_device()
    if device == "mps" or (not args.device and torch.backends.mps.is_available()):
        print("SUCCESS: Production OM-1.0 training on Apple Silicon GPU (MPS)")

    config_path = Path(args.config or ROOT / "configs" / "om-1.0-local.json")
    tok_path = Path(args.tokenizer or ROOT / "artifacts" / "tokenizer-fixed-v3.json")
    data_path = Path(
        args.data
        or ROOT / "data" / "production-corpus" / "clean" / "fineweb-deduped.jsonl"
    )
    if not data_path.is_file():
        alt = ROOT / "knowledge.txt"
        ensure_knowledge_file(alt)
        if (ROOT / "data" / "om-chat-sft-v4-complete.jsonl").is_file():
            data_path = ROOT / "data" / "om-chat-sft-v4-complete.jsonl"
        else:
            data_path = alt

    cfg = ModelConfig.from_json(str(config_path))
    if args.block_size:
        cfg.max_seq_len = int(args.block_size)
    tok = load_tokenizer(str(tok_path))
    cfg.vocab_size = len(tok.vocab)
    model = OMTransformer(cfg)
    out = Path(args.output)
    if not out.is_absolute():
        out = ROOT / out
    tc = TrainingConfig(
        steps=int(args.max_iters),
        batch_size=int(args.batch_size),
        learning_rate=float(args.lr),
        output_dir=str(out.parent),
        checkpoint_every=max(50, int(args.eval_interval)),
        log_every=max(1, int(args.eval_interval) // 5 or 1),
        precision=args.precision,
    )
    trainer = Trainer(model, tc, device=device)
    ds = build_dataset(str(data_path), tok, cfg.max_seq_len)
    print(
        json.dumps(
            {
                "mode": "production",
                "device": str(trainer.device),
                "parameters": model.exact_parameter_count(),
                "dataset_blocks": len(ds),
                "data": str(data_path),
                "architecture": {
                    "rope": True,
                    "rmsnorm": bool(cfg.use_rmsnorm),
                    "swiglu": True,
                    "sdpa": True,
                },
            },
            indent=2,
        ),
        flush=True,
    )
    result = trainer.train(ds)
    latest = Path(tc.output_dir) / "latest.pt"
    if latest.is_file() and out.resolve() != latest.resolve():
        out.parent.mkdir(parents=True, exist_ok=True)
        torch.save(torch.load(latest, map_location="cpu", weights_only=False), out)
        print(f"Also wrote {out}")
    result["friendly_checkpoint"] = str(out)
    return result


# =====================================================================
# 5. CLI
# =====================================================================
def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Train OM-1.0 from scratch on Mac (MPS)")
    p.add_argument(
        "--mode",
        choices=("bpe", "toy", "production"),
        default="bpe",
        help="bpe=sub-word knowledge.txt; toy=char; production=full OM stack",
    )
    p.add_argument("--device", default="", help="mps|cpu|cuda (default: auto, MPS on Mac)")
    p.add_argument("--data", default="", help="Path to knowledge.txt / corpus / jsonl")
    p.add_argument("--config", default="", help="ModelConfig JSON (production)")
    p.add_argument("--tokenizer", default="", help="Local tokenizer JSON (production)")
    p.add_argument(
        "--output",
        default="artifacts/checkpoints/om-1.0-scratch/om1_weights.pt",
        help="Where to save weights",
    )
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--block-size", type=int, default=128)
    p.add_argument("--max-iters", type=int, default=2000)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--eval-interval", type=int, default=200)
    p.add_argument("--n-embd", type=int, default=192)
    p.add_argument("--n-head", type=int, default=6)
    p.add_argument("--n-layer", type=int, default=6)
    p.add_argument("--sample-tokens", type=int, default=120)
    p.add_argument("--vocab-size", type=int, default=5000, help="BPE target vocab size")
    p.add_argument(
        "--train-sample-chars",
        type=int,
        default=2_000_000,
        help="Max chars used to train BPE merges (full file still encoded)",
    )
    p.add_argument("--max-chars", type=int, default=0, help="Optional cap when loading corpus")
    p.add_argument("--precision", default="auto", choices=("auto", "fp32", "fp16", "bf16"))
    p.add_argument(
        "--build-knowledge",
        nargs="*",
        metavar="DIR",
        help="Aggregate offline local docs into knowledge.txt then exit (or continue if --train-after-build)",
    )
    p.add_argument(
        "--knowledge-out",
        default="knowledge.txt",
        help="Output path for --build-knowledge",
    )
    p.add_argument(
        "--train-after-build",
        action="store_true",
        help="After building knowledge.txt, continue into training",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_argparser().parse_args(argv)

    # Offline docs → knowledge.txt (no internet)
    if args.build_knowledge is not None:
        sources = args.build_knowledge or [
            "docs",
            "data/om-foundation-corpus",
            "README.md",
        ]
        result = aggregate_local_docs(sources, args.knowledge_out)
        print(json.dumps({"built_knowledge": result}, indent=2))
        args.data = args.data or args.knowledge_out
        if not args.train_after_build:
            return 0

    if args.mode == "bpe":
        if not args.data:
            args.data = str(ROOT / "knowledge.txt")
        ensure_knowledge_file(Path(args.data))
        if args.batch_size == 16:
            args.batch_size = 32
        run_bpe(args)
    elif args.mode == "toy":
        if args.batch_size == 16:
            args.batch_size = 32
        run_toy(args)
    else:
        run_production(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
