"""STEP 84 — Advanced Learning Intelligence.

Pattern mining → knowledge building → dataset generation → evaluation → improvement plan.
"""
from __future__ import annotations

import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any


class AdvancedLearningIntelligence:
    def __init__(self, out_dir: str | Path | None = None) -> None:
        root = Path(__file__).resolve().parents[3]
        self.out_dir = Path(out_dir or root / "data" / "om-memory" / "advanced_learning")
        self.out_dir.mkdir(parents=True, exist_ok=True)

    def mine_patterns(self, texts: list[str]) -> list[dict[str, Any]]:
        words: Counter[str] = Counter()
        for t in texts:
            for w in re.findall(r"[a-zA-Z]{4,}", (t or "").lower()):
                words[w] += 1
        return [
            {"pattern": w, "count": c, "weight": min(1.0, c / 10)}
            for w, c in words.most_common(25)
            if c >= 2
        ]

    def build_knowledge(self, patterns: list[dict[str, Any]]) -> list[dict[str, str]]:
        knowledge = []
        for p in patterns[:15]:
            knowledge.append(
                {
                    "concept": p["pattern"],
                    "summary": f"Recurring concept '{p['pattern']}' (weight={p['weight']:.2f})",
                    "type": "pattern",
                }
            )
        return knowledge

    def generate_dataset(
        self,
        question: str,
        answer: str,
        *,
        quality_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Produce SFT/DPO-ready examples from a turn."""
        q = (question or "").strip()
        a = (answer or "").strip()
        if not q or not a:
            return []
        examples = [
            {
                "type": "sft",
                "messages": [
                    {"role": "user", "content": q},
                    {"role": "assistant", "content": a},
                ],
                "score": quality_score,
            }
        ]
        if quality_score < 0.55:
            improved = (
                "Provide a clearer, complete answer to the user request.\n"
                f"Request: {q}\n"
                "Answer with structure, verified facts, and next steps."
            )
            examples.append(
                {
                    "type": "dpo",
                    "prompt": q,
                    "chosen": improved,
                    "rejected": a[:800],
                }
            )
        return examples

    def evaluate_learning(self, examples: list[dict[str, Any]]) -> dict[str, Any]:
        sft = sum(1 for e in examples if e.get("type") == "sft")
        dpo = sum(1 for e in examples if e.get("type") == "dpo")
        return {
            "examples": len(examples),
            "sft": sft,
            "dpo": dpo,
            "ready_for_training": len(examples) > 0,
        }

    def improve(
        self,
        question: str,
        answer: str,
        quality: dict[str, Any] | None = None,
        history_texts: list[str] | None = None,
    ) -> dict[str, Any]:
        quality = quality or {}
        score = float(quality.get("score") or 0.0)
        patterns = self.mine_patterns((history_texts or []) + [question, answer])
        knowledge = self.build_knowledge(patterns)
        dataset = self.generate_dataset(question, answer, quality_score=score)
        evaluation = self.evaluate_learning(dataset)
        plan = []
        if score < 0.55:
            plan.append("Generate DPO preference pair from weak answer")
            plan.append("Retrain lightly with new preference data")
        else:
            plan.append("Add successful turn to SFT buffer")
        plan.append("Update pattern knowledge store")

        stamp = int(time.time())
        out = {
            "step": 84,
            "patterns": patterns,
            "knowledge": knowledge,
            "dataset": dataset,
            "evaluation": evaluation,
            "plan": plan,
            "ts": stamp,
        }
        (self.out_dir / f"record_{stamp}.json").write_text(
            json.dumps(out, indent=2)[:50000], encoding="utf-8"
        )
        # append training buffer
        buf = self.out_dir / "training_buffer.jsonl"
        with buf.open("a", encoding="utf-8") as f:
            for ex in dataset:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
        return out
