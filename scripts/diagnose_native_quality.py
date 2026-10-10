#!/usr/bin/env python3
"""Diagnose native OM generation quality without hosted LLMs or modifying artifacts.

This report separates load/integrity problems from weakly trained or mismatched
weights. It does not claim that a successful load proves answer quality.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import torch

from om_ai.backends.om_native import OMNativeBackend, default_native_paths
from om_ai.tokenizer import load_tokenizer, tokenizer_fingerprint
from om_ai.runtime.engine import is_degenerate_generation

PROMPTS = [
    "Hi! Please introduce yourself in one sentence.",
    "Explain why the sky appears blue in simple language.",
    "What is 17 multiplied by 23? Show the calculation.",
    "Return valid JSON only: {\"name\": \"OM\", \"skills\": [\"chat\", \"coding\"]}",
]


def checkpoint_metadata(path: str) -> dict[str, Any]:
    p = Path(path)
    result: dict[str, Any] = {"path": str(p), "exists": p.is_file()}
    if not p.is_file():
        return result
    result["bytes"] = p.stat().st_size
    try:
        ck = torch.load(p, map_location="cpu", weights_only=False)
        result["container_type"] = type(ck).__name__
        if isinstance(ck, dict):
            result["top_level_keys"] = sorted(str(k) for k in ck.keys())[:100]
            result["global_step"] = ck.get("global_step")
            result["epoch"] = ck.get("epoch")
            result["best_loss"] = ck.get("best_loss")
            extra = ck.get("extra")
            if isinstance(extra, dict):
                # Only non-secret training/model metadata is reported.
                allowed = (
                    "model_name", "trained", "tokenizer_path",
                    "tokenizer_fingerprint", "tokenizer_sha256",
                    "config_path", "global_step", "training_stage",
                    "dataset", "dataset_name", "steps", "loss",
                )
                result["extra"] = {k: extra[k] for k in allowed if k in extra}
            state = ck.get("model", ck)
            if isinstance(state, dict):
                result["tensor_count"] = sum(
                    1 for value in state.values() if isinstance(value, torch.Tensor)
                )
                result["nonfinite_tensor_count"] = sum(
                    1 for value in state.values()
                    if isinstance(value, torch.Tensor) and not torch.isfinite(value).all().item()
                )
                emb = state.get("token_embedding.weight")
                result["embedding_shape"] = list(emb.shape) if isinstance(emb, torch.Tensor) else None
                head = state.get("lm_head.weight")
                result["lm_head_shape"] = list(head.shape) if isinstance(head, torch.Tensor) else None
    except Exception as exc:
        result["inspection_error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> int:
    paths = default_native_paths()
    report: dict[str, Any] = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "native_only": True,
        "paths": paths,
        "checkpoint_metadata": checkpoint_metadata(paths.get("checkpoint", "")),
    }
    tokenizer_path = paths.get("tokenizer", "")
    if tokenizer_path and Path(tokenizer_path).is_file():
        try:
            tok = load_tokenizer(tokenizer_path)
            report["requested_tokenizer"] = {
                "path": tokenizer_path,
                "fingerprint": tokenizer_fingerprint(tokenizer_path),
                "vocab_size": len(tok.vocab),
                "inspection": tok.inspect() if hasattr(tok, "inspect") else {},
            }
            sample = "The sky appears blue because air scatters shorter blue wavelengths."
            ids = tok.encode(sample, add_bos=True, add_eos=True)
            report["tokenizer_round_trip"] = {
                "input": sample,
                "token_count": len(ids),
                "decoded": tok.decode(ids),
                "round_trip_exact": tok.decode(ids).strip() == sample.strip(),
                "min_id": min(ids) if ids else None,
                "max_id": max(ids) if ids else None,
            }
        except Exception as exc:
            report["tokenizer_error"] = f"{type(exc).__name__}: {exc}"

    backend = OMNativeBackend()
    try:
        report["load"] = backend.load(require_checkpoint=True)
    except Exception as exc:
        report["load_error"] = f"{type(exc).__name__}: {exc}"
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2

    report["actual_loaded_tokenizer"] = {
        "path": backend.engine.tokenizer_path,
        "fingerprint": backend.engine.tokenizer_fingerprint,
        "vocab_size": len(backend.engine.tokenizer.vocab),
        "model_vocab_size": int(backend.engine.model.cfg.vocab_size),
        "max_seq_len": int(backend.engine.model.cfg.max_seq_len),
        "parameters": backend.engine.model.exact_parameter_count(),
        "device": str(backend.engine.device),
    }
    results = []
    for prompt in PROMPTS:
        started = time.perf_counter()
        try:
            answer = backend.chat(
                [{"role": "user", "content": prompt}],
                max_new_tokens=96,
                temperature=0.0,
                top_k=1,
                top_p=1.0,
                repetition_penalty=1.0,
                min_new_tokens=1,
                no_repeat_ngram_size=0,
            )
            results.append({
                "prompt": prompt,
                "answer": answer,
                "seconds": round(time.perf_counter() - started, 3),
                "degenerate": is_degenerate_generation(answer),
                "nonempty": bool((answer or "").strip()),
            })
        except Exception as exc:
            results.append({
                "prompt": prompt,
                "error": f"{type(exc).__name__}: {exc}",
                "seconds": round(time.perf_counter() - started, 3),
            })
    report["greedy_generation"] = results
    report["quality_summary"] = {
        "prompts": len(results),
        "nonempty_answers": sum(bool(x.get("nonempty")) for x in results),
        "degenerate_answers": sum(bool(x.get("degenerate")) for x in results),
        "all_answers_nonempty_and_nondegenerate": all(
            x.get("nonempty") and not x.get("degenerate") for x in results
        ),
        "warning": (
            "This diagnostic checks integrity and obvious degeneration, not full semantic correctness. "
            "Use scripts/evaluate_om_capabilities.py for capability checks."
        ),
    }
    output = Path("artifacts/evaluations/om-native-quality-diagnostic.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"report_path": str(output), "quality_summary": report["quality_summary"]}, indent=2))
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["quality_summary"]["all_answers_nonempty_and_nondegenerate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
