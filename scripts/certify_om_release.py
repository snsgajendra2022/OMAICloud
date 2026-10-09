#!/usr/bin/env python3
"""Fail-closed release certification for OM's native checkpoint.

This is a local integration gate, not a standardized benchmark. It does not call a
hosted model. A missing checkpoint, incompatible tokenizer, load error, or unusable
native output is a failure; the script never substitutes a canned response.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(args: argparse.Namespace) -> dict[str, Any]:
    from om_ai.backends.om_native import OMNativeBackend, default_native_paths
    from om_ai.runtime.engine import is_degenerate_generation, usable_generation_text
    from om_ai.tokenizer import load_tokenizer, tokenizer_fingerprint

    paths = default_native_paths()
    report: dict[str, Any] = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_revision": args.revision or None,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "device_requested": args.device or paths.get("device") or "auto",
        "checks": {},
        "generation_cases": [],
        "certified": False,
        "limitations": [
            "Passing smoke prompts does not establish semantic quality or frontier-model parity.",
            "Training data provenance, tenant isolation, multimodal trained weights, load testing, and rollback need separate gates.",
            "Run against the exact checkpoint and tokenizer intended for deployment."
        ],
    }

    def check(name: str, ok: bool, **details: Any) -> None:
        report["checks"][name] = {"status": "PASS" if ok else "FAIL", **details}

    tokenizer_path = Path(paths["tokenizer"])
    checkpoint_path = Path(paths["checkpoint"]) if paths.get("checkpoint") else None
    config_path = Path(paths["config"])
    check("config_exists", config_path.is_file(), path=str(config_path))
    check("tokenizer_exists", tokenizer_path.is_file(), path=str(tokenizer_path))
    check("checkpoint_exists", bool(checkpoint_path and checkpoint_path.is_file()),
          path=str(checkpoint_path) if checkpoint_path else None)

    if tokenizer_path.is_file():
        try:
            tokenizer = load_tokenizer(tokenizer_path)
            vocab_size = getattr(tokenizer, "vocab_size", None)
            if vocab_size is None:
                vocab_size = len(getattr(tokenizer, "vocab", {}))
            fingerprint = tokenizer_fingerprint(tokenizer_path)
            check("tokenizer_loads", True, vocab_size=int(vocab_size), fingerprint=fingerprint,
                  bos_id=getattr(tokenizer, "bos_id", None),
                  eos_id=getattr(tokenizer, "eos_id", None),
                  pad_id=getattr(tokenizer, "pad_id", None),
                  unk_id=getattr(tokenizer, "unk_id", None))
            sample = "OM tokenizer round-trip: café, नमस्ते, Python."
            encoded = tokenizer.encode(sample)
            decoded = tokenizer.decode(encoded)
            check("tokenizer_encode_decode", bool(encoded) and isinstance(decoded, str) and bool(decoded.strip()),
                  token_count=len(encoded), decoded_preview=decoded[:160])
        except Exception as exc:
            check("tokenizer_loads", False, error=f"{type(exc).__name__}: {exc}")
            check("tokenizer_encode_decode", False, blocked_by="tokenizer_loads")
    else:
        check("tokenizer_loads", False, blocked_by="tokenizer_exists")
        check("tokenizer_encode_decode", False, blocked_by="tokenizer_exists")

    if args.no_generate:
        check("checkpoint_loads", False, skipped=True, reason="--no-generate requested")
        check("native_generation", False, skipped=True, reason="--no-generate requested")
    elif not (config_path.is_file() and tokenizer_path.is_file()
              and checkpoint_path and checkpoint_path.is_file()):
        check("checkpoint_loads", False, blocked_by="missing config/tokenizer/checkpoint")
        check("native_generation", False, blocked_by="checkpoint_loads")
    else:
        backend = OMNativeBackend()
        try:
            started = time.perf_counter()
            info = backend.load(
                config_path=str(config_path),
                tokenizer_path=str(tokenizer_path),
                checkpoint_path=str(checkpoint_path),
                device=args.device or paths.get("device") or None,
                require_checkpoint=True,
            )
            check("checkpoint_loads", bool(backend.loaded and backend.health().get("ok")),
                  load_seconds=round(time.perf_counter() - started, 3),
                  device=info.get("device"), model=info.get("name"),
                  checkpoint_sha256=sha256_file(checkpoint_path),
                  tokenizer_fingerprint=info.get("tokenizer_fingerprint"),
                  model_vocab_size=info.get("vocab_size") or getattr(
                      getattr(backend.engine.model, "cfg", None), "vocab_size", None))
        except Exception as exc:
            check("checkpoint_loads", False, error=f"{type(exc).__name__}: {exc}")
            check("native_generation", False, blocked_by="checkpoint_loads")
        else:
            prompts = [
                ("greeting", "User: Hello. Reply with a short greeting."),
                ("knowledge", "User: What is Python? Explain in one sentence."),
                ("coding", "User: Write a Python function that adds two numbers."),
                ("math", "User: Calculate 17 * 23. Give the result."),
                ("instruction", "User: Give exactly two tips for clear writing."),
                ("context", "User: My project uses React. What framework did I mention?"),
            ]
            generation_started = time.perf_counter()
            for category, prompt in prompts:
                item: dict[str, Any] = {"category": category, "prompt": prompt}
                try:
                    started = time.perf_counter()
                    answer = backend.generate(
                        prompt,
                        max_new_tokens=args.max_new_tokens,
                        temperature=0.2,
                        top_p=0.9,
                        top_k=40,
                    )
                    answer = str(answer or "").strip()
                    usable = bool(usable_generation_text(answer))
                    degenerate = bool(is_degenerate_generation(answer))
                    item.update({
                        "status": "PASS" if usable and not degenerate else "FAIL",
                        "answer": answer[:1200],
                        "usable": usable,
                        "degenerate": degenerate,
                        "latency_seconds": round(time.perf_counter() - started, 3),
                    })
                except Exception as exc:
                    item.update({"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})
                report["generation_cases"].append(item)
            failed = [case for case in report["generation_cases"] if case["status"] != "PASS"]
            check("native_generation", not failed, cases=len(report["generation_cases"]),
                  passed=len(report["generation_cases"]) - len(failed),
                  failed=len(failed),
                  total_seconds=round(time.perf_counter() - generation_started, 3))

    critical = ("config_exists", "tokenizer_exists", "checkpoint_exists",
                "tokenizer_loads", "tokenizer_encode_decode", "checkpoint_loads",
                "native_generation")
    report["certified"] = all(
        report["checks"].get(key, {}).get("status") == "PASS" for key in critical
    )
    report["release_status"] = "CERTIFIED_SMOKE_ONLY" if report["certified"] else "NOT_CERTIFIED"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/audit/om_release_certification.json")
    parser.add_argument("--revision", default="")
    parser.add_argument("--device", default=None, help="cpu, mps, or cuda; defaults to OM config")
    parser.add_argument("--max-new-tokens", type=int, default=48)
    parser.add_argument("--no-generate", action="store_true",
                        help="run only the artifact/tokenizer preflight; always reports NOT_CERTIFIED")
    args = parser.parse_args()
    if args.max_new_tokens < 1 or args.max_new_tokens > 512:
        parser.error("--max-new-tokens must be between 1 and 512")
    report = run(args)
    output = (ROOT / args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {
        "release_status": report["release_status"],
        "checks": {name: item["status"] for name, item in report["checks"].items()},
        "generation": {
            "passed": sum(x.get("status") == "PASS" for x in report["generation_cases"]),
            "total": len(report["generation_cases"]),
        },
        "report": str(output.relative_to(ROOT)),
    }
    print(json.dumps(summary, indent=2))
    return 0 if report["certified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
