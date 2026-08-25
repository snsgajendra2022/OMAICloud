"""Generate SFT/preference training rows from weaknesses."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def generate_examples(
    question: str,
    old_answer: str,
    weaknesses: list[dict[str, Any]],
    *,
    out_dir: str | Path = "data/om_training/improvements",
) -> dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    preferred = _preferred(question, weaknesses)
    row = {
        "prompt": question,
        "response": preferred,
        "rejected": (old_answer or "")[:2000],
        "source": "om-improvement-engine",
        "weak_areas": [w.get("area") for w in weaknesses],
        "ts": time.time(),
    }
    sft_path = out / "sft_improvements.jsonl"
    pref_path = out / "preference_improvements.jsonl"
    with sft_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"prompt": question, "response": preferred, "source": row["source"]}, ensure_ascii=False) + "\n")
    with pref_path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "prompt": question,
                    "chosen": preferred,
                    "rejected": row["rejected"],
                    "source": row["source"],
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    # area-specific shard
    for w in weaknesses:
        area = str(w.get("area") or "general")
        shard = out / f"{area}.jsonl"
        with shard.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {
        "created": True,
        "sft_path": str(sft_path),
        "preference_path": str(pref_path),
        "preferred_preview": preferred[:400],
        "weak_areas": row["weak_areas"],
    }


def _preferred(question: str, weaknesses: list[dict[str, Any]]) -> str:
    hints = "\n".join(f"- {w.get('hint')}" for w in weaknesses) or "- Be clear and complete"
    return (
        f"Question: {question}\n\n"
        "## Understanding\n"
        f"Address the user ask directly: {question[:200]}\n\n"
        "## Requirements from evaluator\n"
        f"{hints}\n\n"
        "## Solution\n"
        "Provide a structured, correct, secure answer with validation/tests when coding. "
        "Never invent citations. Prefer architecture → implementation → validation.\n"
    )
