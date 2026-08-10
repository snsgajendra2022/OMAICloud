#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import shutil
from pathlib import Path


def size_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return total


def main():
    ap = argparse.ArgumentParser(description="OM-70B training preflight")
    ap.add_argument("--config", default="configs/70b.json")
    ap.add_argument("--data", required=True)
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--min-data-bytes", type=int, default=1_000_000_000)
    args = ap.parse_args()

    config = Path(args.config)
    data = Path(args.data)
    tokenizer = Path(args.tokenizer)

    report = {
        "config": {"ok": config.is_file(), "path": str(config)},
        "data": {"ok": False, "path": str(data), "bytes": 0},
        "tokenizer": {"ok": tokenizer.is_file(), "path": str(tokenizer)},
        "cuda": {"ok": False},
        "deepspeed": {"ok": shutil.which("deepspeed") is not None},
        "ready": False,
    }

    if data.exists():
        report["data"]["bytes"] = size_bytes(data)
        report["data"]["ok"] = report["data"]["bytes"] >= args.min_data_bytes

    try:
        raw = json.loads(tokenizer.read_text(encoding="utf-8"))
        vocab = raw.get("vocab", {})
        report["tokenizer"]["vocab_size"] = len(vocab)
        report["tokenizer"]["chat_tokens"] = all(
            t in vocab
            for t in ("<system>", "</system>", "<user>", "</user>", "<assistant>", "</assistant>")
        )
        report["tokenizer"]["ok"] = report["tokenizer"]["ok"] and report["tokenizer"]["chat_tokens"]
    except Exception as exc:
        report["tokenizer"]["ok"] = False
        report["tokenizer"]["error"] = str(exc)

    try:
        import torch
        gpus = []
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                p = torch.cuda.get_device_properties(i)
                gpus.append({
                    "index": i,
                    "name": p.name,
                    "vram_gb": round(p.total_memory / (1024**3), 2),
                })
        report["cuda"] = {
            "ok": torch.cuda.is_available() and len(gpus) > 0,
            "gpu_count": len(gpus),
            "gpus": gpus,
            "mps_available": bool(
                getattr(torch.backends, "mps", None)
                and torch.backends.mps.is_available()
            ),
        }
    except Exception as exc:
        report["cuda"] = {"ok": False, "error": str(exc)}

    report["ready"] = all(
        report[k]["ok"] for k in ("config", "data", "tokenizer", "cuda", "deepspeed")
    )

    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["ready"] else 2)


if __name__ == "__main__":
    main()
