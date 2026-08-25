"""Learning layer — feedback → datasets → improvement hints."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from om_ai.continuous.cycle import export_learning_bundle
from om_ai.continuous.feedback import FeedbackStore


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
    return {"id": fid, "stored": True}


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
                "then": "om-ai sft / om-ai dpo + om-ai eval suite",
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
