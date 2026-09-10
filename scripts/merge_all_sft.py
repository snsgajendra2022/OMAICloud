#!/usr/bin/env python3
"""Merge all OM SFT-like JSONL corpora into data/training/om_all_sft_merged.jsonl."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "training" / "om_all_sft_merged.jsonl"
KEYS = (
    "distillation_sft",
    "training_buffer",
    "om_dataset",
    "sft.jsonl",
    "sft_improvements",
    "general_qa",
    "om-training/sft",
    "training/sft",
    "test_training/sft",
    "om_learning/training_queue",
    "om-chat-sft",
    "om-feedback-sft",
    "om-sft",
    "om10_english",
    "example_sft",
)


def main() -> None:
    paths: list[Path] = []
    for p in ROOT.rglob("*.jsonl"):
        s = str(p).replace("\\", "/")
        if any(x in s for x in ("/.venv/", "/__pycache__/", "/om_all_sft_merged")):
            continue
        if any(k in s for k in KEYS):
            paths.append(p)

    seen: set[str] = set()
    n = 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as w:
        for p in sorted(set(paths)):
            try:
                lines = p.read_text(encoding="utf-8").splitlines()
            except Exception:
                continue
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                prompt = response = None
                messages = None
                if isinstance(row.get("messages"), list):
                    messages = row["messages"]
                    for m in messages:
                        if m.get("role") == "user":
                            prompt = m.get("content")
                        if m.get("role") == "assistant":
                            response = m.get("content")
                elif row.get("instruction") and (row.get("output") or row.get("response")):
                    prompt = row["instruction"]
                    response = row.get("output") or row.get("response")
                    messages = [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": response},
                    ]
                elif row.get("prompt") and row.get("response"):
                    prompt = row["prompt"]
                    response = row["response"]
                    messages = [
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": response},
                    ]
                elif isinstance(row.get("example"), dict) and row["example"].get("messages"):
                    messages = row["example"]["messages"]
                    for m in messages:
                        if m.get("role") == "user":
                            prompt = m.get("content")
                        if m.get("role") == "assistant":
                            response = m.get("content")
                if not (prompt and response):
                    continue
                key = str(prompt)[:500] + "\n" + str(response)[:500]
                if key in seen:
                    continue
                seen.add(key)
                w.write(
                    json.dumps(
                        {
                            "prompt": prompt,
                            "response": response,
                            "messages": messages,
                            "source": str(p.relative_to(ROOT)),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                n += 1
    print(f"MERGED {n} examples -> {OUT}")


if __name__ == "__main__":
    main()
