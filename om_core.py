#!/usr/bin/env python3
"""om_core.py — OM Level-1 production scratch engine (MPS).

Self-contained Level-1 chat path with:
  - Pre-LN + SwiGLU + SDPA attention
  - Repetition-penalized generation
  - Date / math tool router (Level-2/3 foundations)
  - Checkpoint save/load so weights survive terminal restarts

Honest scope: this improves Level-1 fluency scaffolding. It is **not** ChatGPT
and **not** Level-5 AGI. For full OM-1.0 production weights use ``om-ai serve``.

Examples
--------
  .venv/bin/python om_core.py --demo
  .venv/bin/python om_core.py --train --iters 1500 --checkpoint artifacts/om_core/weights.pt
  .venv/bin/python om_core.py --chat --checkpoint artifacts/om_core/weights.pt
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import operator
import os
import re
import sys
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# =====================================================================
# 1. HARDWARE
# =====================================================================
def pick_device(preferred: str | None = None) -> torch.device:
    pref = (preferred or os.getenv("OM_DEVICE") or "").strip().lower()
    if pref:
        return torch.device(pref)
    if torch.backends.mps.is_available():
        print("SUCCESS: Running OM Core on Apple Silicon GPU (MPS)")
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    print("WARNING: MPS not found; using CPU")
    return torch.device("cpu")


# =====================================================================
# 2. TOOLS (safe date + math — no unrestricted eval)
# =====================================================================
class OMTools:
    _OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    @staticmethod
    def get_current_date() -> str:
        now = dt.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')} ({now.strftime('%H:%M')})."

    @classmethod
    def _eval_node(cls, node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return cls._eval_node(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and type(node.op) in cls._OPS:
            return cls._OPS[type(node.op)](cls._eval_node(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in cls._OPS:
            return cls._OPS[type(node.op)](cls._eval_node(node.left), cls._eval_node(node.right))
        raise ValueError("unsupported expression")

    @classmethod
    def calculate_math(cls, expression: str) -> str:
        clean = "".join(c for c in expression if c in "0123456789+-*/().% ")
        if not clean.strip():
            return "I could not parse that math expression."
        try:
            tree = ast.parse(clean, mode="eval")
            result = cls._eval_node(tree)
            if float(result).is_integer():
                result = int(result)
            return f"{clean.strip()} = {result}"
        except Exception:
            return "Invalid mathematical expression."


# =====================================================================
# 3. DEFAULT SFT CORPUS (chat + tool-call patterns)
# =====================================================================
DEFAULT_CORPUS = """
<|user|> What day is it today? <|assistant|> CALL_TOOL:date()
<|user|> What is today's date? <|assistant|> CALL_TOOL:date()
<|user|> What is 45 * 12 + 100? <|assistant|> CALL_TOOL:math(45 * 12 + 100)
<|user|> Calculate 10 + 20 <|assistant|> CALL_TOOL:math(10 + 20)
<|user|> Hello! Who are you? <|assistant|> Hello, I am OM. I am a custom AI system built from scratch. How can I help you today?
<|user|> Hi <|assistant|> Hi! How can I help you today?
<|user|> I feel completely stuck writing code. <|assistant|> I understand coding can be frustrating. Take a deep breath, isolate the error message, and let's trace the bugs together step-by-step.
<|user|> Thanks <|assistant|> You're welcome. I'm here if you need anything else.
"""


# =====================================================================
# 4. MODEL (Pre-LN + SwiGLU + SDPA)
# =====================================================================
class SwiGLUBlock(nn.Module):
    def __init__(self, n_embd: int):
        super().__init__()
        self.w1 = nn.Linear(n_embd, 4 * n_embd, bias=False)
        self.w2 = nn.Linear(n_embd, 4 * n_embd, bias=False)
        self.w3 = nn.Linear(4 * n_embd, n_embd, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.w3(F.silu(self.w1(x)) * self.w2(x))


class UpgradedAttention(nn.Module):
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
            scores = q @ k.transpose(-2, -1) * (self.head_size**-0.5)
            scores = scores.masked_fill(self.tril[:t, :t] == 0, float("-inf"))
            out = F.softmax(scores, dim=-1) @ v
        return self.proj(out.transpose(1, 2).contiguous().view(b, t, c))


class StableTransformerBlock(nn.Module):
    def __init__(self, n_embd: int, n_head: int, block_size: int):
        super().__init__()
        self.sa = UpgradedAttention(n_embd, n_head, block_size)
        self.ffwd = SwiGLUBlock(n_embd)
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.sa(self.ln1(x))  # Pre-LN
        x = x + self.ffwd(self.ln2(x))
        return x


class OM1Model(nn.Module):
    def __init__(self, vocab_size: int, n_embd: int, n_head: int, n_layer: int, block_size: int):
        super().__init__()
        self.block_size = block_size
        self.token_embedding_table = nn.Embedding(vocab_size, n_embd)
        self.position_embedding_table = nn.Embedding(block_size, n_embd)
        self.blocks = nn.Sequential(
            *[StableTransformerBlock(n_embd, n_head, block_size) for _ in range(n_layer)]
        )
        self.ln_f = nn.LayerNorm(n_embd)
        self.lm_head = nn.Linear(n_embd, vocab_size)

    def forward(self, idx: torch.Tensor, targets: torch.Tensor | None = None):
        _b, t = idx.shape
        device = idx.device
        x = self.token_embedding_table(idx) + self.position_embedding_table(
            torch.arange(t, device=device)
        )
        x = self.ln_f(self.blocks(x))
        logits = self.lm_head(x)
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def advanced_generate(
        self,
        idx: torch.Tensor,
        max_new_tokens: int,
        temperature: float = 0.7,
        repetition_penalty: float = 1.2,
    ) -> torch.Tensor:
        self.eval()
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size :]
            logits, _ = self(idx_cond)
            next_logits = logits[:, -1, :] / max(temperature, 1e-6)
            for token in set(idx_cond[0].tolist()):
                val = next_logits[0, token]
                next_logits[0, token] = val / repetition_penalty if val > 0 else val * repetition_penalty
            probs = F.softmax(next_logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, next_token), dim=1)
        return idx


# =====================================================================
# 5. CHAR VOCAB + TRAIN / CHECKPOINT
# =====================================================================
def build_char_tables(text: str):
    chars = sorted(set(text))
    stoi = {ch: i for i, ch in enumerate(chars)}
    itos = {i: ch for i, ch in enumerate(chars)}
    return chars, stoi, itos


def save_checkpoint(path: Path, model: OM1Model, meta: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.state_dict(), "meta": meta, "engine": "om_core"}, path)
    print(f"Saved checkpoint → {path}")


def load_checkpoint(path: Path, device: torch.device) -> tuple[OM1Model, dict]:
    blob = torch.load(path, map_location=device, weights_only=False)
    meta = blob["meta"]
    model = OM1Model(
        vocab_size=meta["vocab_size"],
        n_embd=meta["n_embd"],
        n_head=meta["n_head"],
        n_layer=meta["n_layer"],
        block_size=meta["block_size"],
    ).to(device)
    model.load_state_dict(blob["model"])
    return model, meta


def train_model(args: argparse.Namespace) -> Path:
    device = pick_device(args.device or None)
    corpus = DEFAULT_CORPUS * int(args.corpus_repeat)
    if args.data and Path(args.data).is_file():
        corpus = Path(args.data).read_text(encoding="utf-8", errors="ignore") + "\n" + corpus

    chars, stoi, itos = build_char_tables(corpus)
    encode = lambda s: [stoi[c] for c in s if c in stoi]
    data = torch.tensor(encode(corpus), dtype=torch.long)
    n = int(0.9 * len(data))
    train_data = data[:n]

    def get_batch():
        ix = torch.randint(len(train_data) - args.block_size, (args.batch_size,))
        x = torch.stack([train_data[i : i + args.block_size] for i in ix])
        y = torch.stack([train_data[i + 1 : i + args.block_size + 1] for i in ix])
        return x.to(device), y.to(device)

    model = OM1Model(
        vocab_size=len(chars),
        n_embd=args.n_embd,
        n_head=args.n_head,
        n_layer=args.n_layer,
        block_size=args.block_size,
    ).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    print(
        json.dumps(
            {
                "engine": "om_core",
                "level_claim": "Level-1 scaffold (not L5)",
                "device": str(device),
                "vocab": len(chars),
                "params": sum(p.numel() for p in model.parameters()),
                "iters": args.iters,
            }
        ),
        flush=True,
    )
    model.train()
    for step in range(args.iters):
        xb, yb = get_batch()
        _, loss = model(xb, yb)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if step % args.eval_interval == 0 or step == args.iters - 1:
            print(f"Step {step:4d} | loss {loss.item():.4f}", flush=True)

    out = Path(args.checkpoint)
    if not out.is_absolute():
        out = ROOT / out
    meta = {
        "chars": chars,
        "vocab_size": len(chars),
        "n_embd": args.n_embd,
        "n_head": args.n_head,
        "n_layer": args.n_layer,
        "block_size": args.block_size,
    }
    save_checkpoint(out, model, meta)
    return out


# =====================================================================
# 6. AGENT ROUTER
# =====================================================================
def _route_tools_from_text(text: str, user_prompt: str) -> str | None:
    if "CALL_TOOL:date" in text or re.search(
        r"\b(what('?s| is)?\s+today|current date|what day|today'?s date)\b",
        user_prompt,
        re.I,
    ):
        if not re.search(r"[\+\-\*/]", user_prompt):
            return OMTools.get_current_date()
    if "CALL_TOOL:math" in text:
        m = re.search(r"math\(([^)]*)\)", text)
        expr = m.group(1) if m else ""
        return OMTools.calculate_math(expr)
    if re.search(r"[\+\-\*/]", user_prompt) and re.search(
        r"\b(calc|calculate|what is|math)\b", user_prompt, re.I
    ):
        m = re.search(r"(\d[\d\.\s\+\-\*/()]*)", user_prompt)
        if m:
            return OMTools.calculate_math(m.group(1).strip())
    return None


def run_agent_inference(model: OM1Model, meta: dict, user_prompt: str, device: torch.device) -> str:
    # Deterministic tool short-circuit for Level-1 reliability
    direct = _route_tools_from_text("", user_prompt)
    if direct:
        return direct

    stoi = {ch: i for i, ch in enumerate(meta["chars"])}
    itos = {i: ch for i, ch in enumerate(meta["chars"])}
    encode = lambda s: [stoi[c] for c in s if c in stoi]
    decode = lambda ids: "".join(itos.get(i, "") for i in ids)

    formatted = f"<|user|> {user_prompt} <|assistant|> "
    context = torch.tensor([encode(formatted)], dtype=torch.long, device=device)
    if context.numel() == 0:
        return "How can I help you today?"
    out = model.advanced_generate(context, max_new_tokens=64)[0].tolist()
    generated = decode(out[context.size(1) :])
    tool = _route_tools_from_text(generated, user_prompt)
    if tool:
        return tool
    clean = generated.split("<|user|>")[0].strip()
    clean = re.sub(r"CALL_TOOL:\w+\([^)]*\)", "", clean).strip()
    return clean or "How can I help you today?"


def run_demo(args: argparse.Namespace) -> None:
    ckpt = train_model(args)
    device = pick_device(args.device or None)
    model, meta = load_checkpoint(ckpt, device)
    print("\nTESTING RUNTIME ROUTER:")
    for q in (
        "What day is it today?",
        "What is 10 + 20?",
        "Hello! Who are you?",
    ):
        print(f"User: {q}")
        print(f"OM:   {run_agent_inference(model, meta, q, device)}\n")


def run_chat(args: argparse.Namespace) -> None:
    device = pick_device(args.device or None)
    path = Path(args.checkpoint)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        raise SystemExit(f"Missing checkpoint {path}. Run --train or --demo first.")
    model, meta = load_checkpoint(path, device)
    print("OM Core chat (type quit to exit). Level-1 scaffold.")
    while True:
        try:
            q = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q or q.lower() in {"quit", "exit"}:
            break
        print("OM>", run_agent_inference(model, meta, q, device))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="OM Core Level-1 engine (MPS)")
    p.add_argument("--demo", action="store_true", help="Short train + router tests")
    p.add_argument("--train", action="store_true")
    p.add_argument("--chat", action="store_true")
    p.add_argument("--device", default="")
    p.add_argument("--data", default="")
    p.add_argument("--checkpoint", default="artifacts/om_core/weights.pt")
    p.add_argument("--iters", type=int, default=800)
    p.add_argument("--eval-interval", type=int, default=100)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--block-size", type=int, default=128)
    p.add_argument("--n-embd", type=int, default=256)
    p.add_argument("--n-head", type=int, default=8)
    p.add_argument("--n-layer", type=int, default=6)
    p.add_argument("--lr", type=float, default=5e-4)
    p.add_argument("--corpus-repeat", type=int, default=200)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.demo:
        args.iters = min(args.iters, 400)
        run_demo(args)
    elif args.train:
        train_model(args)
    elif args.chat:
        run_chat(args)
    else:
        args.demo = True
        args.iters = 300
        run_demo(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
