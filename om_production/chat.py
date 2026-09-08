"""Production chatbot CLI — history, temperature, repetition penalty, final_response extract."""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

import torch
import torch.nn.functional as F

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


def extract_final(text: str) -> str:
    if "<|final_response|>" in text:
        part = text.split("<|final_response|>", 1)[1]
        part = part.split("<|user|>")[0]
        part = part.split("<|eos|>")[0]
        return part.strip()
    # Strip thought blocks if present
    cleaned = re.sub(r"<\|thought\|>.*?(?=<\|final_response\|>|$)", "", text, flags=re.S)
    cleaned = cleaned.replace("<|assistant|>", "").replace("<|eos|>", "")
    cleaned = cleaned.split("<|user|>")[0].strip()
    return cleaned or text.strip()


@torch.no_grad()
def generate_response(
    model: OMProductionLLM,
    tokenizer: OMTokenizer,
    prompt_text: str,
    device: torch.device,
    *,
    max_new_tokens: int = 150,
    temperature: float = 0.7,
    repetition_penalty: float = 1.3,
) -> str:
    context_tokens = tokenizer.encode(prompt_text)
    idx = torch.tensor([context_tokens], dtype=torch.long, device=device)
    eos_id = tokenizer.encoder.get("<|eos|>", -1)
    user_id = tokenizer.encoder.get("<|user|>", -1)

    for _ in range(max_new_tokens):
        idx_cond = idx[:, -model.block_size :]
        logits, _ = model(idx_cond)
        token_logits = logits[:, -1, :] / max(temperature, 1e-6)
        for token_id in set(idx_cond[0].tolist()):
            val = token_logits[0, token_id]
            token_logits[0, token_id] = (
                val / repetition_penalty if val > 0 else val * repetition_penalty
            )
        probs = F.softmax(token_logits, dim=-1)
        next_token = torch.multinomial(probs, num_samples=1)
        idx = torch.cat((idx, next_token), dim=1)
        tid = int(next_token.item())
        if tid == eos_id or tid == user_id:
            break

    response_ids = idx[0].tolist()[len(context_tokens) :]
    return extract_final(tokenizer.decode(response_ids))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="OM production chat console")
    p.add_argument("--weights", default=str(HERE / "om_chatgpt_level_weights.pt"))
    p.add_argument("--tokenizer", default=str(HERE / "om_tokenizer.json"))
    p.add_argument("--device", default="")
    p.add_argument("--max-new-tokens", type=int, default=150)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--repetition-penalty", type=float, default=1.3)
    args = p.parse_args(argv)

    device = pick_device(args.device or None)
    tokenizer = OMTokenizer()
    tok_path = Path(args.tokenizer)
    if not tok_path.is_file():
        raise SystemExit(f"Missing {tok_path}. Run: python3 tokenizer.py")
    tokenizer.load(tok_path)

    weights = Path(args.weights)
    if not weights.is_file():
        raise SystemExit(
            f"Missing {weights}. Run: python3 train.py  (after tokenizer.py)"
        )

    blob = torch.load(weights, map_location=device, weights_only=False)
    if isinstance(blob, dict) and "model" in blob:
        meta = blob.get("meta") or {}
        state = blob["model"]
        vocab_size = int(meta.get("vocab_size") or len(tokenizer.encoder))
        n_embd = int(meta.get("n_embd") or 256)
        n_head = int(meta.get("n_head") or 8)
        n_layer = int(meta.get("n_layer") or 6)
        block_size = int(meta.get("block_size") or 256)
    else:
        state = blob
        vocab_size = len(tokenizer.encoder)
        n_embd, n_head, n_layer, block_size = 256, 8, 6, 256

    model = OMProductionLLM(vocab_size, n_embd, n_head, n_layer, block_size).to(device)
    model.load_state_dict(state)
    model.eval()
    print("System weights database fully read into memory cache.")
    print("\nOM PRODUCTION CONSOLE ONLINE (Type 'exit' to close connection)")
    print("=" * 66)

    history: list[str] = []
    while True:
        try:
            user_query = input("\nUser: ")
        except (EOFError, KeyboardInterrupt):
            print("\nConnection severed safely.")
            break
        if user_query.strip().lower() in {"exit", "quit"}:
            print("Connection severed safely.")
            break
        if not user_query.strip():
            continue

        # Keep last few turns for context, prune to block window via encode length
        history.append(f"<|user|>{user_query}<|assistant|>")
        structured = "".join(history[-4:])
        ids = tokenizer.encode(structured)
        if len(ids) > model.block_size - 32:
            structured = history[-1]
        print("Thinking...")
        ai_output = generate_response(
            model,
            tokenizer,
            structured,
            device,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            repetition_penalty=args.repetition_penalty,
        )
        history[-1] = f"<|user|>{user_query}<|assistant|><|final_response|>{ai_output}<|eos|>\n"
        print(f"\nOM: {ai_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
