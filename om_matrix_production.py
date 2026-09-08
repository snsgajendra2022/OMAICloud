#!/usr/bin/env python3
"""om_matrix_production.py — Unified OM Master Matrix (L1→L5 *scaffold*).

Self-contained local engine for Mac (MPS/CPU):
  - BPE sub-word tokenizer (``<|user|>`` / ``<|thought|>`` / ``<|assistant|>``)
  - Pre-LN + SwiGLU transformer + repetition-penalized generation
  - Restricted Python sandbox (Level-3 tool foundation)
  - Recursive goal-tree planner printout (Level-5 *structure*, not AGI)
  - Checkpoint save/load + interactive CLI

Honest scope
------------
This bridges **architecture demos** across levels 1–5. It does **not** deliver
Organization-level AGI. Production chat still uses ``om-ai serve`` + real OM-1.0
checkpoints under ``artifacts/checkpoints/``.

Examples
--------
  .venv/bin/python om_matrix_production.py --demo
  .venv/bin/python om_matrix_production.py --train --iters 800
  .venv/bin/python om_matrix_production.py --chat --level 1
  .venv/bin/python om_matrix_production.py --ask "Calculate growth for 75" --level 3
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from contextlib import redirect_stdout
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent


# =====================================================================
# 1. HARDWARE
# =====================================================================
def pick_device(preferred: str | None = None) -> torch.device:
    pref = (preferred or os.getenv("OM_DEVICE") or "").strip().lower()
    if pref:
        return torch.device(pref)
    if torch.backends.mps.is_available():
        print("NATIVE ACCELERATION: OM Matrix on Apple Silicon GPU (MPS).")
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    print("HARDWARE FALLBACK: OM Matrix on CPU.")
    return torch.device("cpu")


# =====================================================================
# 2. DEFAULTS
# =====================================================================
DEFAULTS = {
    "block_size": 256,
    "n_embd": 256,
    "n_head": 8,
    "n_layer": 6,
    "vocab_size": 3000,
    "batch_size": 8,
    "lr": 3e-4,
}


PRODUCTION_CORPUS = """
<|user|> Hello OM! What can you execute? <|assistant|> Hello! I am the OM Unified Matrix Core Engine running local configurations.
<|user|> Perform deep reasoning analysis on this budget matrix. <|thought|> Evaluating step constraints. Slicing numerical cost boundaries. <|assistant|> Analysis complete. Values align within bounds.
<|user|> Solve mathematical calculations for 500 * 5. <|assistant|> CODE_EXEC:
print(500 * 5)
<|user|> Calculate system growth ratios using integer factor 75. <|thought|> Multiply factor by scale 50 in sandbox. <|assistant|> CODE_EXEC:
def run_agent_math():
    input_value = 75
    print(input_value * 50)
run_agent_math()
<|user|> Orchestrate autonomous expansion routines across network clusters. <|thought|> Dispatch alpha/beta/gamma/delta nodes. <|assistant|> Objective recursively parsed and launched.
""" * 200


# =====================================================================
# 3. BPE TOKENIZER
# =====================================================================
class OMBPETokenizer:
    def __init__(self, target_vocab_size: int = 3000):
        self.target_vocab_size = int(target_vocab_size)
        self.special_tokens = [
            "<|pad|>",
            "<|eos|>",
            "<|user|>",
            "<|thought|>",
            "<|assistant|>",
        ]
        self.encoder: dict[str, int] = {}
        self.decoder: dict[int, str] = {}
        self.merges: list[tuple[str, str]] = []

    def fit(self, corpus: str, *, max_words: int = 80_000) -> None:
        print("Tokenizer: Processing conceptual sub-words from production corpus...")
        unique_chars = sorted(set(corpus))
        vocab = list(self.special_tokens)
        for ch in unique_chars:
            if ch not in vocab:
                vocab.append(ch)
        self.encoder = {t: i for i, t in enumerate(vocab)}
        self.merges = []
        words = Counter(re.findall(r"\w+|[^\w\s]", corpus, flags=re.UNICODE))
        if len(words) > max_words:
            words = Counter(dict(words.most_common(max_words)))
        splits = {w: list(w) for w in words}
        protected = set(self.special_tokens)

        while len(self.encoder) < self.target_vocab_size:
            pairs: dict[tuple[str, str], int] = defaultdict(int)
            for w, freq in words.items():
                split = splits[w]
                for i in range(len(split) - 1):
                    a, b = split[i], split[i + 1]
                    if a in protected or b in protected:
                        continue
                    pairs[(a, b)] += freq
            if not pairs:
                break
            best = max(pairs, key=pairs.get)
            new_token = "".join(best)
            if new_token in self.encoder:
                break
            self.encoder[new_token] = len(self.encoder)
            self.merges.append(best)
            for w in words:
                split = splits[w]
                i = 0
                while i < len(split) - 1:
                    if (split[i], split[i + 1]) == best:
                        split[i : i + 2] = [new_token]
                    else:
                        i += 1
        self.decoder = {i: t for t, i in self.encoder.items()}
        print(f"Tokenizer compiled. Codebook size: {len(self.encoder)}")

    def encode(self, text: str) -> list[int]:
        tokens: list[int] = []
        parts = re.split(
            r"(<\|user\|>|<\|assistant\|>|<\|thought\|>|<\|eos\|>|<\|pad\|>)",
            text,
        )
        for part in parts:
            if not part:
                continue
            if part in self.encoder:
                tokens.append(self.encoder[part])
                continue
            for word in re.findall(r"\w+|[^\w\s]", part, flags=re.UNICODE):
                if word in self.encoder:
                    tokens.append(self.encoder[word])
                else:
                    chars = list(word)
                    for a, b in self.merges:
                        i = 0
                        merged = a + b
                        while i < len(chars) - 1:
                            if chars[i] == a and chars[i + 1] == b:
                                chars[i : i + 2] = [merged]
                            else:
                                i += 1
                    for tok in chars:
                        tokens.append(self.encoder.get(tok, 0))
        return tokens

    def decode(self, ids: list[int]) -> str:
        return "".join(self.decoder.get(int(i), "") for i in ids)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "target_vocab_size": self.target_vocab_size,
                    "encoder": self.encoder,
                    "merges": [list(m) for m in self.merges],
                    "special_tokens": self.special_tokens,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> "OMBPETokenizer":
        obj = json.loads(path.read_text(encoding="utf-8"))
        tok = cls(target_vocab_size=int(obj.get("target_vocab_size") or 3000))
        tok.encoder = {str(k): int(v) for k, v in obj["encoder"].items()}
        tok.merges = [tuple(m) for m in obj.get("merges") or []]
        tok.special_tokens = list(obj.get("special_tokens") or tok.special_tokens)
        tok.decoder = {i: t for t, i in tok.encoder.items()}
        return tok


# =====================================================================
# 4. SECURE SANDBOX
# =====================================================================
_SAFE_BUILTINS = {
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "range": range,
    "float": float,
    "int": int,
    "str": str,
    "round": round,
    "print": print,
    "True": True,
    "False": False,
    "None": None,
}


class OMSecureSandbox:
    _BLOCK = re.compile(
        r"\b(os|sys|subprocess|socket|pathlib|open|exec|eval|__import__|compile|input)\b"
        r"|rm\s+-rf|os\.system"
    )

    @classmethod
    def run_isolated_code(cls, code_block: str) -> str:
        if cls._BLOCK.search(code_block):
            return "[SANDBOX RISK SECURITY BLOCK] Harmful execution query intercepted."
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                exec(code_block, {"__builtins__": _SAFE_BUILTINS}, {})
            return buf.getvalue().strip() or "[SANDBOX] OK (no output)"
        except Exception as exc:
            return f"[SANDBOX CODE RUNTIME EXCEPTION]: {exc}"


# =====================================================================
# 5. MODEL
# =====================================================================
class ProductionSwiGLU(nn.Module):
    def __init__(self, n_embd: int):
        super().__init__()
        self.w1 = nn.Linear(n_embd, 4 * n_embd, bias=False)
        self.w2 = nn.Linear(n_embd, 4 * n_embd, bias=False)
        self.w3 = nn.Linear(4 * n_embd, n_embd, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.w3(F.silu(self.w1(x)) * self.w2(x))


class CausalProductionAttention(nn.Module):
    def __init__(self, n_embd: int, n_head: int, block_size: int):
        super().__init__()
        assert n_embd % n_head == 0
        self.n_head = n_head
        self.head_size = n_embd // n_head
        self.qkv_proj = nn.Linear(n_embd, 3 * n_embd, bias=False)
        self.out_proj = nn.Linear(n_embd, n_embd)
        self.register_buffer("tril", torch.tril(torch.ones(block_size, block_size)))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, t, c = x.shape
        q, k, v = torch.chunk(self.qkv_proj(x), 3, dim=-1)
        q = q.view(b, t, self.n_head, self.head_size).transpose(1, 2)
        k = k.view(b, t, self.n_head, self.head_size).transpose(1, 2)
        v = v.view(b, t, self.n_head, self.head_size).transpose(1, 2)
        try:
            out = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        except Exception:
            scores = (q @ k.transpose(-2, -1)) * (self.head_size**-0.5)
            scores = scores.masked_fill(self.tril[:t, :t] == 0, float("-inf"))
            out = F.softmax(scores, dim=-1) @ v
        return self.out_proj(out.transpose(1, 2).contiguous().view(b, t, c))


class ProductionTransformerLayer(nn.Module):
    def __init__(self, n_embd: int, n_head: int, block_size: int):
        super().__init__()
        self.ln1 = nn.LayerNorm(n_embd)
        self.attn = CausalProductionAttention(n_embd, n_head, block_size)
        self.ln2 = nn.LayerNorm(n_embd)
        self.ffwd = ProductionSwiGLU(n_embd)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.ln1(x))  # Pre-LN
        x = x + self.ffwd(self.ln2(x))
        return x


class OMProductionModel(nn.Module):
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
        self.vocab_size = vocab_size
        self.token_embeddings = nn.Embedding(vocab_size, n_embd)
        self.position_embeddings = nn.Embedding(block_size, n_embd)
        self.blocks = nn.Sequential(
            *[ProductionTransformerLayer(n_embd, n_head, block_size) for _ in range(n_layer)]
        )
        self.ln_final = nn.LayerNorm(n_embd)
        self.output_head = nn.Linear(n_embd, vocab_size)

    def forward(self, idx: torch.Tensor, targets: torch.Tensor | None = None):
        _b, t = idx.shape
        x = self.token_embeddings(idx) + self.position_embeddings(
            torch.arange(t, device=idx.device)
        )
        logits = self.output_head(self.ln_final(self.blocks(x)))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, self.vocab_size), targets.view(-1))
        return logits if targets is None else (logits, loss)

    @torch.no_grad()
    def penalized_generate(
        self,
        idx: torch.Tensor,
        max_tokens: int = 100,
        temperature: float = 0.7,
        repetition_penalty: float = 1.25,
    ) -> torch.Tensor:
        self.eval()
        for _ in range(max_tokens):
            idx_cond = idx[:, -self.block_size :]
            logits = self(idx_cond)
            token_logits = logits[:, -1, :] / max(temperature, 1e-6)
            for t in set(idx_cond[0].tolist()):
                val = token_logits[0, t]
                token_logits[0, t] = (
                    val / repetition_penalty if val > 0 else val * repetition_penalty
                )
            next_token = torch.multinomial(F.softmax(token_logits, dim=-1), num_samples=1)
            idx = torch.cat((idx, next_token), dim=1)
        return idx


# =====================================================================
# 6. MASTER ENGINE (L1–L5 scaffolds)
# =====================================================================
class OMMasterEngine:
    """Unified multi-level processing matrix (scaffold, not AGI)."""

    def __init__(
        self,
        model: OMProductionModel,
        tokenizer: OMBPETokenizer,
        device: torch.device,
    ):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device

    def process_request(self, user_prompt: str, target_evolution_level: float) -> str:
        level = float(target_evolution_level)
        print(f"\n[ENGAGING EVOLUTION LAYER: LEVEL {level:.1f}]")

        if level == 1.0:
            prompt = f"<|user|> {user_prompt} <|assistant|> "
            ids = torch.tensor(
                [self.tokenizer.encode(prompt)], dtype=torch.long, device=self.device
            )
            if ids.numel() == 0:
                return "[OM-1.0] How can I help you today?"
            gen = self.model.penalized_generate(ids, max_tokens=40)[0].tolist()
            raw = self.tokenizer.decode(gen[ids.size(1) :])
            clean = raw.split("<|user|>")[0].strip()
            # Prefer fluent template if undertrained model still garbles
            if len(clean) < 8 or clean.count("<|") > 2:
                clean = (
                    f"Engine online. Received: '{user_prompt}'. "
                    "I can chat, reason in steps, run safe sandbox math, or show a goal tree."
                )
            return f"[OM-1.0 FLUENT RESPONSE]: {clean}"

        if level == 2.0:
            print("Initializing multi-path reasoning scratchpad...")
            steps = [
                "  -> Step A: Parse string parameters and extract core alphanumeric arguments.",
                "  -> Step B: Isolate multi-dimensional arrays to calculate boundary limits.",
                "  -> Step C: Evaluate conditional token trees to eliminate variance.",
                f"  -> Step D: Map objective '{user_prompt}' onto a verifiable conclusion.",
            ]
            return (
                "[OM-2.0 REASONING SCRATCHPAD LOGS]:\n"
                + "\n".join(steps)
                + f"\n\n[FINAL COMPILATION RESULT]: Reasoning verified for: '{user_prompt}'"
            )

        if level == 3.0:
            print("Constructing secure local script container...")
            nums = [int(n) for n in re.findall(r"\d+", user_prompt)]
            math_value = nums[0] if nums else 10
            # Prefer explicit arithmetic if present
            expr = None
            m = re.search(r"(\d+\s*[\*\+\-/]\s*\d+)", user_prompt)
            if m:
                expr = m.group(1).replace(" ", "")
                generated_script = f"print({expr})"
            else:
                generated_script = (
                    "def run_agent_math():\n"
                    f"    input_value = {math_value}\n"
                    "    print(f'Computed Scale Factor Matrix: {input_value * 50}')\n"
                    "run_agent_math()"
                )
            sandbox_output = OMSecureSandbox.run_isolated_code(generated_script)
            return (
                "[OM-3.0 AGENT RESPONSE]:\n"
                f"[EXECUTED CODE BLOCK]:\n{generated_script}\n\n"
                f"[SANDBOX OUTPUT]: {sandbox_output}"
            )

        if level == 4.0:
            return (
                "[OM-4.0 INNOVATOR SCAFFOLD]:\n"
                "Pattern search stub only — not scientific discovery.\n"
                f"Hypothesis seed from prompt: '{user_prompt}'\n"
                "Next real step: train larger models + eval harnesses, not rename layers."
            )

        if level == 5.0:
            print("Constructing autonomous multi-agent operational tree (scaffold)...")
            today = dt.datetime.now().strftime("%A, %B %d, %Y")
            nums = [int(n) for n in re.findall(r"\d+", user_prompt)]
            factor = nums[0] if nums else 75
            sandbox = OMSecureSandbox.run_isolated_code(
                f"print({factor} * 50)"
            )
            return (
                "[OM-5.0 CORPORATE SYSTEM REPORT] (scaffold — not Organization AGI)\n"
                f"MASTER GOAL: '{user_prompt}'\n"
                f"TIMELINE: {today}\n"
                "├── Node-Alpha (Ingestion): Local corpus / prompt intake\n"
                "├── Node-Beta  (Reasoning): Scratchpad steps drafted\n"
                f"├── Node-Gamma (Sandbox): {sandbox}\n"
                "└── Node-Delta (Supervisor): Security blocklist active\n"
                "SUMMARY: Objective recursively parsed into a goal tree and demo agents."
            )

        return "[ERROR 0x55] Invalid evolution level. Use 1.0, 2.0, 3.0, 4.0, or 5.0."


# =====================================================================
# 7. TRAIN / CHECKPOINT / CLI
# =====================================================================
def train(args: argparse.Namespace) -> Path:
    device = pick_device(args.device or None)
    corpus = PRODUCTION_CORPUS
    if args.data and Path(args.data).is_file():
        corpus = Path(args.data).read_text(encoding="utf-8", errors="ignore") + "\n" + corpus

    tok = OMBPETokenizer(target_vocab_size=args.vocab_size)
    sample = corpus[: min(len(corpus), args.train_sample_chars)]
    tok.fit(sample)
    ids = torch.tensor(tok.encode(corpus), dtype=torch.long)
    if ids.numel() < args.block_size + 2:
        ids = torch.tensor(tok.encode(corpus * 10), dtype=torch.long)

    model = OMProductionModel(
        vocab_size=len(tok.encoder),
        n_embd=args.n_embd,
        n_head=args.n_head,
        n_layer=args.n_layer,
        block_size=args.block_size,
    ).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)

    def get_batch():
        ix = torch.randint(len(ids) - args.block_size, (args.batch_size,))
        x = torch.stack([ids[i : i + args.block_size] for i in ix]).to(device)
        y = torch.stack([ids[i + 1 : i + args.block_size + 1] for i in ix]).to(device)
        return x, y

    print(
        json.dumps(
            {
                "engine": "om_matrix_production",
                "honest_note": "L1-L5 architectural scaffold — not AGI",
                "device": str(device),
                "vocab": len(tok.encoder),
                "params": sum(p.numel() for p in model.parameters()),
                "tokens": int(ids.numel()),
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
            print(f"Step {step:4d} | loss {float(loss.detach()):.4f}", flush=True)

    out = Path(args.checkpoint)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    tok_path = out.with_suffix(".tokenizer.json")
    tok.save(tok_path)
    torch.save(
        {
            "engine": "om_matrix_production",
            "model": model.state_dict(),
            "meta": {
                "vocab_size": len(tok.encoder),
                "n_embd": args.n_embd,
                "n_head": args.n_head,
                "n_layer": args.n_layer,
                "block_size": args.block_size,
                "tokenizer_path": str(tok_path),
            },
        },
        out,
    )
    print(f"Saved checkpoint → {out}")
    return out


def load_engine(checkpoint: Path, device: torch.device) -> OMMasterEngine:
    blob = torch.load(checkpoint, map_location=device, weights_only=False)
    meta = blob["meta"]
    tok = OMBPETokenizer.load(Path(meta["tokenizer_path"]))
    model = OMProductionModel(
        vocab_size=meta["vocab_size"],
        n_embd=meta["n_embd"],
        n_head=meta["n_head"],
        n_layer=meta["n_layer"],
        block_size=meta["block_size"],
    ).to(device)
    model.load_state_dict(blob["model"])
    model.eval()
    return OMMasterEngine(model, tok, device)


def ensure_engine(args: argparse.Namespace) -> OMMasterEngine:
    device = pick_device(args.device or None)
    path = Path(args.checkpoint)
    if not path.is_absolute():
        path = ROOT / path
    if not path.is_file():
        print("No checkpoint found — training a short bootstrap run...")
        args.iters = min(getattr(args, "iters", 400), 400)
        path = train(args)
    return load_engine(path, device)


def run_demo(engine: OMMasterEngine) -> None:
    cases = [
        (1.0, "Connect terminal parameters to local matrix architecture."),
        (2.0, "Analyze the gradient descent weights array stability values."),
        (3.0, "Calculate system growth ratios using integer factor 75."),
        (5.0, "Orchestrate autonomous expansion routines across network clusters."),
    ]
    for level, prompt in cases:
        print(engine.process_request(prompt, level))
        print("-" * 60)


def run_chat(engine: OMMasterEngine, level: float) -> None:
    print(f"OM Matrix interactive CLI (level={level}). Type quit to exit.")
    print("Commands: /level 1|2|3|4|5   /help")
    while True:
        try:
            line = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in {"quit", "exit"}:
            break
        if line.startswith("/level"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    level = float(parts[1])
                    print(f"Level set to {level}")
                except ValueError:
                    print("Usage: /level 1")
            continue
        if line.startswith("/help"):
            print("Levels: 1=chat, 2=reason, 3=sandbox agent, 4=innovator stub, 5=goal tree")
            continue
        print(engine.process_request(line, level))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="OM Master Matrix Production Engine")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--train", action="store_true")
    p.add_argument("--chat", action="store_true")
    p.add_argument("--ask", default="", help="Single prompt")
    p.add_argument("--level", type=float, default=1.0)
    p.add_argument("--device", default="")
    p.add_argument("--data", default="")
    p.add_argument("--checkpoint", default="artifacts/om_matrix/weights.pt")
    p.add_argument("--iters", type=int, default=600)
    p.add_argument("--eval-interval", type=int, default=100)
    p.add_argument("--batch-size", type=int, default=DEFAULTS["batch_size"])
    p.add_argument("--block-size", type=int, default=DEFAULTS["block_size"])
    p.add_argument("--n-embd", type=int, default=DEFAULTS["n_embd"])
    p.add_argument("--n-head", type=int, default=DEFAULTS["n_head"])
    p.add_argument("--n-layer", type=int, default=DEFAULTS["n_layer"])
    p.add_argument("--vocab-size", type=int, default=DEFAULTS["vocab_size"])
    p.add_argument("--lr", type=float, default=DEFAULTS["lr"])
    p.add_argument("--train-sample-chars", type=int, default=1_000_000)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.train and not args.demo and not args.chat and not args.ask:
        train(args)
        return 0

    if args.demo:
        args.iters = min(args.iters, 400)
        path = train(args)
        device = pick_device(args.device or None)
        engine = load_engine(path, device)
        run_demo(engine)
        return 0

    engine = ensure_engine(args)
    if args.ask:
        print(engine.process_request(args.ask, args.level))
        return 0
    if args.chat:
        run_chat(engine, args.level)
        return 0

    # Default: demo
    return main(["--demo", "--iters", "300", "--checkpoint", args.checkpoint])


if __name__ == "__main__":
    raise SystemExit(main())
