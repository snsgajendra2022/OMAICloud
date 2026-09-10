"""STEP 93 — Model Training Intelligence (OM-native).

Brain-facing training control plane for SFT / DPO / eval on local OM checkpoints.
This does not magically create a ChatGPT-scale model; it wires real OM training hooks.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ModelTrainingIntelligence:
    def __init__(self) -> None:
        root = Path(__file__).resolve().parents[3]
        self.root = root
        self.buffer = root / "data" / "om-memory" / "advanced_learning" / "training_buffer.jsonl"
        self.recipes_dir = root / "data" / "om-memory" / "training_recipes"
        self.recipes_dir.mkdir(parents=True, exist_ok=True)

    def inventory(self) -> dict[str, Any]:
        info: dict[str, Any] = {
            "step": 93,
            "model": "OM-1.0",
            "buffer_exists": self.buffer.exists(),
            "buffer_examples": 0,
            "checkpoints": [],
            "capabilities": ["sft", "dpo", "eval", "safety_scan"],
        }
        if self.buffer.exists():
            try:
                info["buffer_examples"] = sum(1 for _ in self.buffer.open())
            except Exception:
                pass
        try:
            from om_ai.training.checkpoint import list_checkpoints

            info["checkpoints"] = list_checkpoints()[:10]
        except Exception:
            # fallback scan
            for p in (self.root / "artifacts").glob("**/*"):
                if p.is_dir() and "om" in p.name.lower():
                    info["checkpoints"].append(str(p))
                    if len(info["checkpoints"]) >= 10:
                        break
        return info

    def build_recipe(
        self,
        *,
        stage: str = "sft",
        notes: str = "",
    ) -> dict[str, Any]:
        inv = self.inventory()
        recipe = {
            "step": 93,
            "stage": stage,
            "model": "OM-1.0",
            "data_buffer": str(self.buffer),
            "examples": inv.get("buffer_examples", 0),
            "pipeline": [
                "collect_experiences",
                "filter_quality",
                "build_sft_or_dpo_set",
                "train_local_om",
                "evaluate",
                "safety_tune",
                "promote_checkpoint",
            ],
            "commands": {
                "sft": "om-ai sft --help",
                "dpo": "om-ai dpo --help",
                "eval": "python -m pytest tests/test_brain.py -q",
            },
            "notes": notes
            or "Use local OM checkpoint; scale model size separately when hardware allows.",
            "honest_limit": (
                "ChatGPT-level quality still requires larger pretrained weights + "
                "much more data/compute. This module manages the OM training loop."
            ),
        }
        out = self.recipes_dir / f"recipe_{stage}.json"
        out.write_text(json.dumps(recipe, indent=2), encoding="utf-8")
        recipe["recipe_path"] = str(out)
        return recipe

    def prepare_from_turn(
        self,
        question: str,
        answer: str,
        quality: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        quality = quality or {}
        score = float(quality.get("score") or 0.0)
        self.buffer.parent.mkdir(parents=True, exist_ok=True)
        example = {
            "type": "sft" if score >= 0.55 else "dpo_seed",
            "messages": [
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer},
            ],
            "score": score,
        }
        with self.buffer.open("a", encoding="utf-8") as f:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
        return {
            "step": 93,
            "queued": True,
            "example_type": example["type"],
            "inventory": self.inventory(),
            "recipe": self.build_recipe(stage="sft" if score >= 0.55 else "dpo"),
        }
