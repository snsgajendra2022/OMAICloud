#!/usr/bin/env python3
"""Inspect raw OM native generation before chat quality filtering.

This is a local debugging tool. It intentionally prints the raw decoded candidate
and token IDs; do not expose its output to end users or treat it as a quality pass.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from om_ai.backends.om_native import OMNativeBackend, default_native_paths
from om_ai.runtime.engine import fit_messages_to_context


def _checkpoint_metadata(path: str) -> dict:
    """Read small metadata fields without printing model tensors."""
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, dict):
        return {"payload_type": type(payload).__name__}
    result = {}
    for key in ("stage", "step", "epoch", "global_step", "model_config", "train_config", "sft_config", "dpo_config", "extra", "metadata"):
        value = payload.get(key)
        if isinstance(value, (str, int, float, bool, dict, list, type(None))):
            result[key] = value
    if isinstance(payload.get("model"), dict):
        result["tensor_count"] = len(payload["model"])
        result["embedding_shape"] = list(payload["model"]["token_embedding.weight"].shape) if "token_embedding.weight" in payload["model"] else None
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", default="Hi! Please introduce yourself in one sentence.")
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--top-tokens", type=int, default=10)
    parser.add_argument("--config", help="Explicit model config path (overrides .env)")
    parser.add_argument("--tokenizer", help="Explicit tokenizer path (overrides .env)")
    parser.add_argument("--checkpoint", help="Explicit checkpoint path (overrides .env)")
    parser.add_argument("--device", choices=("mps", "cuda", "cpu"), help="Explicit inference device")
    parser.add_argument("--output", help="Optional JSON report path")
    args = parser.parse_args()

    paths = default_native_paths()
    for key, value in (("config", args.config), ("tokenizer", args.tokenizer), ("checkpoint", args.checkpoint)):
        if value:
            paths[key] = str(Path(value).expanduser().resolve(strict=False))
    if args.device:
        paths["device"] = args.device
    missing = [
        {"asset": key, "path": paths.get(key)}
        for key in ("config", "tokenizer", "checkpoint")
        if not paths.get(key) or not Path(paths[key]).is_file()
    ]
    if missing:
        print(json.dumps({"ok": False, "stage": "preflight", "missing": missing}, indent=2))
        return 2

    backend = OMNativeBackend()
    loaded = backend.load(
        config_path=paths["config"],
        tokenizer_path=paths["tokenizer"],
        checkpoint_path=paths["checkpoint"],
        device=paths.get("device") or None,
        require_checkpoint=True,
    )
    engine = backend.engine
    tokenizer = engine.tokenizer
    model = engine.model
    messages = [{"role": "user", "content": args.prompt}]
    fitted = fit_messages_to_context(messages, tokenizer, model.cfg.max_seq_len)
    prompt_ids = tokenizer.encode_chat(fitted, add_generation_prompt=True, add_eos=False)
    prompt_ids = prompt_ids[-model.cfg.max_seq_len:]
    input_ids = torch.tensor([prompt_ids], dtype=torch.long, device=engine.device)

    with torch.no_grad():
        all_logits = model(input_ids)["logits"]
        first_logits = all_logits[0, -1].float()
        finite_logits = bool(torch.isfinite(first_logits).all().item())
        top_values, top_ids = torch.topk(first_logits, k=min(max(1, args.top_tokens), first_logits.numel()))
        generated = model.generate(
            input_ids,
            max_new_tokens=max(1, args.max_new_tokens),
            temperature=0.0,
            top_k=1,
            top_p=1.0,
            repetition_penalty=1.0,
            eos_token_id=tokenizer.eos_id,
            stop_token_ids=[int(tokenizer.assistant_end_id)] if tokenizer.assistant_end_id is not None else [],
            min_new_tokens=0,
            no_repeat_ngram_size=0,
            repetition_window=0,
        )

    new_ids = [int(token) for token in generated[0, len(prompt_ids):].detach().cpu().tolist()]
    stop_ids = {int(tokenizer.eos_id)}
    if tokenizer.assistant_end_id is not None:
        stop_ids.add(int(tokenizer.assistant_end_id))
    candidate_ids = new_ids
    while candidate_ids and candidate_ids[-1] in stop_ids:
        candidate_ids.pop()

    top = []
    for token_id, score in zip(top_ids.detach().cpu().tolist(), top_values.detach().cpu().tolist()):
        try:
            token_text = tokenizer.decode([int(token_id)])
        except Exception as exc:
            token_text = f"<decode-error:{type(exc).__name__}>"
        top.append({"id": int(token_id), "logit": round(float(score), 5), "decoded": token_text})

    checkpoint = paths.get("checkpoint") or ""
    report = {
        "warning": "Raw local debugging output; it bypasses chat quality filtering and is not a quality pass.",
        "backend": loaded.get("backend"),
        "device": loaded.get("device"),
        "checkpoint": checkpoint,
        "checkpoint_bytes": Path(checkpoint).stat().st_size if checkpoint and Path(checkpoint).is_file() else None,
        "checkpoint_metadata": _checkpoint_metadata(checkpoint) if checkpoint and Path(checkpoint).is_file() else {},
        "tokenizer_path": engine.tokenizer_path,
        "tokenizer_fingerprint": loaded.get("tokenizer_fingerprint"),
        "tokenizer_info": tokenizer.inspect(),
        "config_path": engine.config_path,
        "max_seq_len": model.cfg.max_seq_len,
        "prompt": args.prompt,
        "fitted_messages": fitted,
        "prompt_token_count": len(prompt_ids),
        "prompt_token_ids": prompt_ids,
        "first_next_token_logits_finite": finite_logits,
        "first_next_token_logit_min": float(first_logits.min().item()) if finite_logits else None,
        "first_next_token_logit_max": float(first_logits.max().item()) if finite_logits else None,
        "first_next_token_top_logits": top,
        "generated_token_count_including_stop": len(new_ids),
        "generated_token_ids": new_ids,
        "candidate_token_ids_without_trailing_stop": candidate_ids,
        "raw_candidate": tokenizer.decode(candidate_ids),
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
