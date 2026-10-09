#!/usr/bin/env python3
"""Diagnose OM's self-hosted native checkpoint without calling a hosted LLM."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from om_ai.backends.om_native import OMNativeBackend, default_native_paths
from om_ai.runtime.engine import EMPTY_GENERATION_FALLBACK, is_degenerate_generation, usable_generation_text


def main() -> int:
    paths = default_native_paths()
    report = {
        "backend": "om_native",
        "provider": "OM AI",
        "paths": {
            key: {
                "path": value or None,
                "exists": bool(value and Path(value).is_file()),
                "bytes": Path(value).stat().st_size
                if value and Path(value).is_file() and key == "checkpoint"
                else None,
            }
            for key, value in paths.items()
        },
    }
    print(json.dumps(report, indent=2), flush=True)

    # Fail before allocating model memory when paths are wrong. In particular,
    # a stale .env value must not be mistaken for a missing trained checkpoint.
    missing = [
        (key, value)
        for key, value in paths.items()
        if key in {"config", "tokenizer", "checkpoint"}
        and (not value or not Path(value).is_file())
    ]
    if missing:
        root = Path(__file__).resolve().parents[1]
        available_configs = sorted(
            str(path.relative_to(root)) for path in (root / "configs").glob("*.json")
        )
        print(
            json.dumps(
                {
                    "stage": "preflight",
                    "ok": False,
                    "error_type": "NativeAssetPathError",
                    "missing": [{"asset": key, "path": value or None} for key, value in missing],
                    "available_configs": available_configs,
                    "hint": (
                        "Check .env and exported OM_MODEL_CONFIG / OM_AI_CONFIG values. "
                        "Do not select a different config merely because it exists: "
                        "the config architecture, tokenizer vocabulary, and checkpoint "
                        "must come from the same trained run."
                    ),
                },
                indent=2,
            ),
            flush=True,
        )
        return 2

    backend = OMNativeBackend()
    try:
        loaded = backend.load(require_checkpoint=True)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "stage": "load",
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "hint": (
                        "Confirm OM_MODEL_CONFIG, OM_MODEL_TOKENIZER, and "
                        "OM_MODEL_CHECKPOINT point to files from the same trained run. "
                        "A load success is not a quality pass: token-soup outputs are "
                        "now marked as failed generation checks."
                    ),
                },
                indent=2,
            ),
            flush=True,
        )
        return 2

    print(
        json.dumps(
            {
                "stage": "load",
                "ok": True,
                "device": loaded.get("device"),
                "parameters": loaded.get("parameters"),
                "tokenizer_fingerprint": loaded.get("tokenizer_fingerprint"),
                "checkpoint": loaded.get("checkpoint"),
            },
            indent=2,
        ),
        flush=True,
    )

    prompts = [
        "Hi! Please introduce yourself in one sentence.",
        "Explain why the sky appears blue in simple language.",
        "What is 17 multiplied by 23? Show the calculation.",
    ]
    failures = 0
    for prompt in prompts:
        try:
            answer = backend.chat(
                [{"role": "user", "content": prompt}],
                max_new_tokens=96,
                temperature=0.2,
                top_p=0.9,
                top_k=40,
                repetition_penalty=1.1,
                min_new_tokens=4,
            )
            usable = (bool(usable_generation_text(answer)) and not is_degenerate_generation(answer) and answer.strip() != EMPTY_GENERATION_FALLBACK)
            if not usable:
                failures += 1
            print(
                json.dumps(
                    {
                        "stage": "generation",
                        "ok": usable,
                        "prompt": prompt,
                        "answer": (answer or "")[:1200],
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
        except Exception as exc:
            failures += 1
            print(
                json.dumps(
                    {
                        "stage": "generation",
                        "ok": False,
                        "prompt": prompt,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    print(json.dumps({"stage": "summary", "ok": failures == 0, "failed_prompts": failures}))
    return 0 if failures == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
