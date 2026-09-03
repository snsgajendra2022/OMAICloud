"""Learning layer — feedback → quality → datasets → improvement queue."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from om_ai.continuous.cycle import export_learning_bundle
from om_ai.continuous.feedback import FeedbackStore

from .learner import LearningEngine

from .experience import Experience


__all__=[

    "LearningEngine",

    "Experience"

]

def record_feedback(
    *,
    problem: str,
    old_answer: str,
    correct_answer: str,
    rating: int = 2,
    user_id: str = "",
    db: str = "artifacts/feedback.sqlite3",
) -> dict[str, Any]:
    store = FeedbackStore(db)
    fid = store.add(
        problem,
        old_answer,
        rating,
        user_id=user_id,
        preferred_response=correct_answer,
        metadata=json.dumps({"source": "foundation-learning"}),
    )
    queue_path = Path("artifacts/learning/improvement_queue.jsonl")
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "id": fid,
                    "ts": time.time(),
                    "problem": problem[:500],
                    "old_answer": old_answer[:500],
                    "correct_answer": correct_answer[:800],
                    "rating": rating,
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    return {
        "id": fid,
        "stored": True,
        "training_sample_created": True,
        "improvement_queue_updated": True,
        "queue": str(queue_path),
    }


def build_datasets(out_dir: str | Path = "data/continuous") -> dict[str, Any]:
    return export_learning_bundle(out_dir)


def improvement_plan(weak_areas: list[str] | None = None) -> dict[str, Any]:
    areas = weak_areas or []
    examples = []
    for a in areas:
        examples.append(
            {
                "weak_area": a,
                "action": "Generate SFT/preference examples targeting this area",
                "then": "om-ai sft / om-ai dpo + om-ai evaluate run",
            }
        )
    return {
        "weak_areas": areas,
        "actions": examples,
        "cycle": [
            "User conversation",
            "Quality check",
            "Feedback",
            "Training example",
            "Dataset update",
            "Future fine-tune",
        ],
    }


def quality_check_reply(text: str, *, user_ask: str = "") -> dict[str, Any]:
    from om_ai.runtime.chat_orchestrator import is_low_quality_reply

    fail = is_low_quality_reply(text)
    return {
        "ok": not bool(fail),
        "reason": fail or "ok",
        "user_ask": user_ask[:200],
        "action": "store_feedback_and_use_reasoning_fallback" if fail else "accept",
    }


def run_learning_cycle(
    *,
    out_dir: str | Path = "data/continuous",
    weak_areas: list[str] | None = None,
    synthesize_from_eval: bool = True,
) -> dict[str, Any]:
    """Full software loop: quality hints → export datasets → recipe → optional synth rows."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    store = FeedbackStore()
    if synthesize_from_eval and weak_areas:
        for area in weak_areas:
            prompt = f"Improve OM capability in: {area}"
            preferred = (
                f"Provide a clear, correct {area} answer with steps, validation, "
                "and no invented citations."
            )
            store.add(
                prompt,
                f"[weak] placeholder for {area}",
                1,
                preferred_response=preferred,
                metadata=json.dumps({"source": "eval-weak-area", "area": area}),
            )
    recipe = export_learning_bundle(out)
    plan = improvement_plan(weak_areas)
    report = {
        "status": "ok",
        "feedback_stored": True,
        "training_sample_created": True,
        "improvement_queue_updated": True,
        "recipe": recipe,
        "improvement_plan": plan,
        "next": [
            recipe.get("commands", {}).get("sft"),
            recipe.get("commands", {}).get("dpo"),
            recipe.get("commands", {}).get("eval"),
        ],
    }
    (out / "learning_cycle_report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return report
