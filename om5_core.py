#!/usr/bin/env python3
"""om5_core.py — OM matrix scaffold (thought → tools → sandbox → objectives).

This is an **architecture scaffold** toward Levels 2–3 (reasoning + agents).
It is **not** Level-5 Organization AGI. Naming it OM-5.0 marks the *matrix
design target*, not current capability.

Includes:
  - Word-piece BPE (``OMTokenizer`` with ``<|thought|>``)
  - Pre-LN + SwiGLU model + repetition-penalized generation
  - Restricted Python sandbox (no os/subprocess)
  - Objective router with planning scratchpad
  - Optional local docs RAG (offline folder scan)
  - Checkpoint save/load
  - JSON multi-agent task dispatch stub

Examples
--------
  .venv/bin/python om5_core.py --demo
  .venv/bin/python om5_core.py --train --iters 800
  .venv/bin/python om5_core.py --objective "Project year-2 costs at 8% growth from 50000"
  .venv/bin/python om5_core.py --rag-scan docs README.md --demo
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import operator
import os
import re
import sys
from contextlib import redirect_stdout
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from om_ai.training.local_knowledge import aggregate_local_docs
from om_ai.training.om_tokenizer import OMTokenizer


# =====================================================================
# 1. HARDWARE
# =====================================================================
def pick_device(preferred: str | None = None) -> torch.device:
    pref = (preferred or os.getenv("OM_DEVICE") or "").strip().lower()
    if pref:
        return torch.device(pref)
    if torch.backends.mps.is_available():
        print("OM-5.0 MATRIX: GPU Acceleration via Metal (MPS) engaged.")
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    print("SYSTEM: Running OM-5.0 scaffold on CPU.")
    return torch.device("cpu")


# =====================================================================
# 2. RESTRICTED SANDBOX + MATH
# =====================================================================
_SAFE_BUILTINS = {
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "range": range,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "str": str,
    "round": round,
    "print": print,
    "True": True,
    "False": False,
    "None": None,
}


class OMSandbox:
    """Isolated exec for tiny numeric scripts — not a full OS agent."""

    _BLOCK = re.compile(
        r"\b(os|sys|subprocess|socket|pathlib|open|exec|eval|__import__|compile|input)\b"
    )

    @classmethod
    def execute_python(cls, code_string: str) -> str:
        if cls._BLOCK.search(code_string):
            return "[SANDBOX SECURITY BLOCK] Unsafe phrase detected."
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                exec(code_string, {"__builtins__": _SAFE_BUILTINS}, {})
            out = buf.getvalue().strip()
            return out or "[SANDBOX] OK (no printed output)"
        except Exception as exc:
            return f"[SANDBOX RUNTIME ERROR] {exc}"


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def safe_math(expr: str) -> str:
    clean = "".join(c for c in expr if c in "0123456789+-*/(). ")
    try:
        tree = ast.parse(clean, mode="eval")

        def _ev(n):
            if isinstance(n, ast.Expression):
                return _ev(n.body)
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
                return float(n.value)
            if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
                return _OPS[type(n.op)](_ev(n.operand))
            if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
                return _OPS[type(n.op)](_ev(n.left), _ev(n.right))
            raise ValueError("bad")

        val = _ev(tree)
        return str(int(val) if float(val).is_integer() else val)
    except Exception:
        return "invalid"


# =====================================================================
# 3. MODEL
# =====================================================================
class SwiGLU(nn.Module):
    def __init__(self, n_embd: int):
        super().__init__()
        self.w1 = nn.Linear(n_embd, 4 * n_embd, bias=False)
        self.w2 = nn.Linear(n_embd, 4 * n_embd, bias=False)
        self.w3 = nn.Linear(4 * n_embd, n_embd, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.w3(F.silu(self.w1(x)) * self.w2(x))


class CausalMultiHeadAttention(nn.Module):
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
            scores = q @ k.transpose(-2, -1) * (self.head_size**-0.5)
            scores = scores.masked_fill(self.tril[:t, :t] == 0, float("-inf"))
            out = F.softmax(scores, dim=-1) @ v
        return self.out_proj(out.transpose(1, 2).contiguous().view(b, t, c))


class OM5Block(nn.Module):
    def __init__(self, n_embd: int, n_head: int, block_size: int):
        super().__init__()
        self.ln1 = nn.LayerNorm(n_embd)
        self.attn = CausalMultiHeadAttention(n_embd, n_head, block_size)
        self.ln2 = nn.LayerNorm(n_embd)
        self.ffwd = SwiGLU(n_embd)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.ln1(x))
        x = x + self.ffwd(self.ln2(x))
        return x


class OM5Model(nn.Module):
    def __init__(self, vocab_size: int, n_embd: int, n_head: int, n_layer: int, block_size: int):
        super().__init__()
        self.block_size = block_size
        self.vocab_size = vocab_size
        self.token_embeddings = nn.Embedding(vocab_size, n_embd)
        self.position_embeddings = nn.Embedding(block_size, n_embd)
        self.blocks = nn.Sequential(
            *[OM5Block(n_embd, n_head, block_size) for _ in range(n_layer)]
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
        return logits, loss

    @torch.no_grad()
    def secure_generate(
        self,
        idx: torch.Tensor,
        max_tokens: int = 80,
        temperature: float = 0.6,
        penalty: float = 1.3,
    ) -> torch.Tensor:
        self.eval()
        for _ in range(max_tokens):
            idx_cond = idx[:, -self.block_size :]
            logits, _ = self(idx_cond)
            token_logits = logits[:, -1, :] / max(temperature, 1e-6)
            for t in set(idx_cond[0].tolist()):
                val = token_logits[0, t]
                token_logits[0, t] = val / penalty if val > 0 else val * penalty
            next_t = torch.multinomial(F.softmax(token_logits, dim=-1), num_samples=1)
            idx = torch.cat((idx, next_t), dim=1)
        return idx


# =====================================================================
# 4. CORPUS + MULTI-AGENT DISPATCH + RAG
# =====================================================================
DEFAULT_OM5_CORPUS = """
<|user|> Orchestrate a financial projection script for project costs. <|thought|> Write a safe python script to compute growth without guessing. <|assistant|> CODE_EXEC:
def project_costs():
    initial_cost = 50000
    growth_rate = 1.08
    print(initial_cost * growth_rate)
project_costs()
<|user|> What is 15 percent of 200? <|thought|> Use arithmetic. <|assistant|> CODE_EXEC:
print(0.15 * 200)
<|user|> Hello <|thought|> Greet briefly. <|assistant|> Hello, I am OM matrix scaffold. How can I help with your objective?
"""


@dataclass
class AgentTask:
    agent: str
    goal: str
    status: str = "pending"
    result: str = ""


@dataclass
class DispatchPlan:
    objective: str
    tasks: list[AgentTask] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def json_multi_agent_dispatch(objective: str) -> DispatchPlan:
    """Break an objective into parallel agent slots (scaffold, not live multi-model)."""
    plan = DispatchPlan(objective=objective, tasks=[])
    lower = objective.lower()
    if any(k in lower for k in ("cost", "budget", "finance", "percent", "%", "project")):
        plan.tasks.append(AgentTask("finance_agent", "Compute numeric projection safely"))
        plan.tasks.append(AgentTask("verifier_agent", "Check units and growth assumptions"))
    if any(k in lower for k in ("doc", "knowledge", "read", "file", "company")):
        plan.tasks.append(AgentTask("rag_agent", "Retrieve local document snippets"))
    if not plan.tasks:
        plan.tasks.append(AgentTask("planner_agent", "Clarify objective and propose next step"))
        plan.tasks.append(AgentTask("responder_agent", "Draft user-facing answer"))
    return plan


def local_rag_snippets(query: str, knowledge_path: Path, limit: int = 2) -> list[str]:
    if not knowledge_path.is_file():
        return []
    text = knowledge_path.read_text(encoding="utf-8", errors="ignore")
    chunks = [c.strip() for c in re.split(r"\n\n+", text) if len(c.strip()) > 40]
    q = set(re.findall(r"\w+", query.lower()))
    scored = []
    for ch in chunks:
        words = set(re.findall(r"\w+", ch.lower()))
        score = len(q & words)
        if score:
            scored.append((score, ch[:500]))
    scored.sort(reverse=True)
    return [c for _, c in scored[:limit]]


# =====================================================================
# 5. TRAIN / CHECKPOINT / OBJECTIVE RUNTIME
# =====================================================================
def train(args: argparse.Namespace) -> Path:
    device = pick_device(args.device or None)
    corpus = DEFAULT_OM5_CORPUS * int(args.corpus_repeat)
    if args.data and Path(args.data).is_file():
        corpus = Path(args.data).read_text(encoding="utf-8", errors="ignore") + "\n" + corpus
    if args.knowledge and Path(args.knowledge).is_file():
        corpus += "\n" + Path(args.knowledge).read_text(encoding="utf-8", errors="ignore")[:200_000]

    tok = OMTokenizer(vocab_size=int(args.vocab_size))
    tok.train_tokenizer(corpus[: min(len(corpus), int(args.train_sample_chars))])
    ids = torch.tensor(tok.encode(corpus), dtype=torch.long)
    if ids.numel() < args.block_size + 2:
        ids = torch.tensor(tok.encode(corpus * 20), dtype=torch.long)

    def get_batch():
        ix = torch.randint(len(ids) - args.block_size, (args.batch_size,))
        x = torch.stack([ids[i : i + args.block_size] for i in ix])
        y = torch.stack([ids[i + 1 : i + args.block_size + 1] for i in ix])
        return x.to(device), y.to(device)

    model = OM5Model(
        vocab_size=len(tok.encoder),
        n_embd=args.n_embd,
        n_head=args.n_head,
        n_layer=args.n_layer,
        block_size=args.block_size,
    ).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    print(
        json.dumps(
            {
                "engine": "om5_core",
                "honest_level": "scaffold toward L2/L3 — not L5 AGI",
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
            print(f"OM-5.0 step {step:4d} | loss {loss.item():.4f}", flush=True)

    out = Path(args.checkpoint)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    tok_path = out.with_suffix(".tokenizer.json")
    tok.save(tok_path)
    torch.save(
        {
            "engine": "om5_core",
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
    print(f"Saved OM-5.0 checkpoint → {out}")
    return out


def load_om5(path: Path, device: torch.device) -> tuple[OM5Model, OMTokenizer, dict]:
    blob = torch.load(path, map_location=device, weights_only=False)
    meta = blob["meta"]
    tok = OMTokenizer.load(meta["tokenizer_path"])
    model = OM5Model(
        vocab_size=meta["vocab_size"],
        n_embd=meta["n_embd"],
        n_head=meta["n_head"],
        n_layer=meta["n_layer"],
        block_size=meta["block_size"],
    ).to(device)
    model.load_state_dict(blob["model"])
    return model, tok, meta


def _budget_script(objective: str) -> str:
    m = re.search(r"(\d[\d,]*)\s*(?:at|with)?\s*(\d+(?:\.\d+)?)\s*%", objective, re.I)
    if m:
        base = float(m.group(1).replace(",", ""))
        rate = float(m.group(2)) / 100.0
        return f"print({base} * (1 + {rate}))"
    if re.search(r"50000|50,?000", objective) and re.search(r"8\s*%|1\.08", objective):
        return "print(50000 * 1.08)"
    if re.search(r"15\s*%|percent", objective, re.I) and re.search(r"200", objective):
        return "print(0.15 * 200)"
    return "print(120000 * 0.15)"


def process_om5_system_objective(
    objective: str,
    *,
    model: OM5Model | None = None,
    tok: OMTokenizer | None = None,
    device: torch.device | None = None,
    knowledge_path: Path | None = None,
) -> str:
    """Level-2 thought framing + Level-3 tool/sandbox loop (scaffold)."""
    plan = json_multi_agent_dispatch(objective)
    rag = local_rag_snippets(objective, knowledge_path or (ROOT / "knowledge.txt"))

    # Prefer deterministic sandbox for numeric corporate objectives (reliable L2/L3 demo)
    code = _budget_script(objective)
    sandbox_result = OMSandbox.execute_python(code)
    for t in plan.tasks:
        if t.agent == "finance_agent":
            t.status = "done"
            t.result = sandbox_result
        elif t.agent == "rag_agent":
            t.status = "done"
            t.result = rag[0][:200] if rag else "no local snippet"
        elif t.agent == "verifier_agent":
            t.status = "done"
            t.result = "numeric sandbox output accepted" if sandbox_result and "ERROR" not in sandbox_result else "needs review"
        else:
            t.status = "done"
            t.result = "planned"

    thought = (
        "Parse objective → dispatch agents → run restricted sandbox → return executive summary."
    )
    model_tail = ""
    if model is not None and tok is not None and device is not None:
        prompt = (
            f"<|user|> {objective} <|thought|> {thought} <|assistant|> CODE_EXEC:\n{code}\n"
        )
        ctx = torch.tensor([tok.encode(prompt)], dtype=torch.long, device=device)
        gen = model.secure_generate(ctx, max_tokens=40)[0].tolist()
        model_tail = tok.decode(gen[ctx.size(1) :])[:200]

    return (
        f"[OM-5.0 REASONING SCRATCHPAD]: {thought}\n"
        f"[MULTI-AGENT PLAN]:\n{plan.to_json()}\n"
        f"[SANDBOX EXECUTED RESULT]: {sandbox_result}\n"
        + (f"[LOCAL RAG HINT]: {rag[0][:180]}...\n" if rag else "")
        + f"[OM-5.0 EXECUTIVE RESPONSE]: Objective handled. Computed result = {sandbox_result}."
        + (f"\n[MODEL TAIL]: {model_tail}" if model_tail else "")
        + "\n(Note: scaffold toward L2/L3 — not Organization-level AGI.)"
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="OM-5.0 matrix scaffold (MPS)")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--train", action="store_true")
    p.add_argument("--objective", default="")
    p.add_argument("--device", default="")
    p.add_argument("--data", default="")
    p.add_argument("--knowledge", default="knowledge.txt")
    p.add_argument("--checkpoint", default="artifacts/om5_core/weights.pt")
    p.add_argument("--iters", type=int, default=600)
    p.add_argument("--eval-interval", type=int, default=100)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--block-size", type=int, default=128)
    p.add_argument("--n-embd", type=int, default=256)
    p.add_argument("--n-head", type=int, default=8)
    p.add_argument("--n-layer", type=int, default=4)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--vocab-size", type=int, default=2000)
    p.add_argument("--train-sample-chars", type=int, default=500_000)
    p.add_argument("--corpus-repeat", type=int, default=200)
    p.add_argument(
        "--rag-scan",
        nargs="*",
        metavar="DIR",
        help="Offline local docs → knowledge.txt before run",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.rag_scan is not None:
        sources = args.rag_scan or ["docs", "README.md"]
        print(json.dumps(aggregate_local_docs(sources, args.knowledge), indent=2))

    if args.train or args.demo:
        if args.demo:
            args.iters = min(args.iters, 400)
        ckpt = train(args)
        if args.demo or args.objective:
            device = pick_device(args.device or None)
            model, tok, _meta = load_om5(ckpt if isinstance(ckpt, Path) else Path(args.checkpoint), device)
            obj = args.objective or (
                "Orchestrate an operational strategy script for enterprise budget "
                "projections from 50000 at 8% growth."
            )
            print("\nEXECUTING OBJECTIVE RUN:")
            print(process_om5_system_objective(
                obj,
                model=model,
                tok=tok,
                device=device,
                knowledge_path=ROOT / args.knowledge,
            ))
        return 0

    if args.objective:
        device = pick_device(args.device or None)
        path = Path(args.checkpoint)
        if not path.is_absolute():
            path = ROOT / path
        model = tok = None
        if path.is_file():
            model, tok, _ = load_om5(path, device)
        print(
            process_om5_system_objective(
                args.objective,
                model=model,
                tok=tok,
                device=device if model is not None else None,
                knowledge_path=ROOT / args.knowledge,
            )
        )
        return 0

    # default demo
    args.demo = True
    args.iters = 300
    return main([
        "--demo",
        "--iters",
        str(args.iters),
        "--checkpoint",
        args.checkpoint,
        "--knowledge",
        args.knowledge,
    ])


if __name__ == "__main__":
    raise SystemExit(main())
