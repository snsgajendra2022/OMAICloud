"""Continuous learning cycle: feedback → datasets → fine-tune recipe."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .feedback import FeedbackStore
from .replay import build_preference_replay, build_sft_replay


def export_learning_bundle(
    out_dir: str | Path = "data/continuous",
    *,
    db_path: str | None = None,
) -> dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    store = FeedbackStore(db_path) if db_path else FeedbackStore()
    sft_path = out / "sft_replay.jsonl"
    pref_path = out / "preference_replay.jsonl"
    n_sft = build_sft_replay(store, str(sft_path))
    n_pref = build_preference_replay(store, str(pref_path))
    recipe = {
        "cycle": [
            "User interaction",
            "Feedback capture",
            "Export SFT + preference JSONL",
            "om-ai sft / om-ai dpo",
            "Eval suite",
            "Promote checkpoint if scores rise",
        ],
        "commands": {
            "sft": (
                "om-ai sft --config configs/omai-20m.json "
                "--tokenizer artifacts/tokenizer-production-65536.json "
                f"--checkpoint <base.pt> --data {sft_path} "
                "--output artifacts/checkpoints/om-continuous-sft --steps 500 --device mps"
            ),
            "dpo": (
                "om-ai dpo --config configs/omai-20m.json "
                "--tokenizer artifacts/tokenizer-production-65536.json "
                f"--checkpoint <sft.pt> --data {pref_path} "
                "--output artifacts/checkpoints/om-continuous-dpo --steps 300 --device mps"
            ),
            "eval": "om-ai eval suite --out artifacts/eval/post-continuous.json",
        },
        "exported": {"sft_rows": n_sft, "preference_rows": n_pref},
        "paths": {"sft": str(sft_path), "preference": str(pref_path)},
    }
    (out / "recipe.json").write_text(json.dumps(recipe, indent=2) + "\n", encoding="utf-8")
    return recipe
