"""OM Self-Improvement Engine — answer → score → weakness → dataset → train queue."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .data_generator import generate_examples
from .evaluator import evaluate_answer
from .trainer_queue import enqueue
from .version_manager import bump_version, current_version
from .weakness_detector import detect_weaknesses


def improve_from_exchange(
    question: str,
    answer: str,
    *,
    out_dir: str | Path = "data/om_training/improvements",
    bump: bool = True,
) -> dict[str, Any]:
    evaluation = evaluate_answer(question, answer)
    weaknesses = detect_weaknesses(evaluation)
    gen: dict[str, Any] = {"created": False}
    job: dict[str, Any] = {}
    if weaknesses:
        gen = generate_examples(question, answer, weaknesses, out_dir=out_dir)
        job = enqueue(
            sft_path=str(gen.get("sft_path") or ""),
            preference_path=str(gen.get("preference_path") or ""),
            reason=",".join(w["area"] for w in weaknesses),
        )
    version = current_version()
    if bump and weaknesses:
        version = bump_version(
            note=f"improve from: {question[:80]}",
            metrics={"overall": evaluation.get("overall"), "weak": [w["area"] for w in weaknesses]},
        )
    report = {
        "status": "improved" if weaknesses else "ok_no_change",
        "evaluation": evaluation,
        "weaknesses": weaknesses,
        "training_data": gen,
        "trainer_job": job,
        "version": version,
        "ts": time.time(),
    }
    rep_dir = Path("artifacts/improvement")
    rep_dir.mkdir(parents=True, exist_ok=True)
    (rep_dir / "latest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def run_sprint1_demo() -> dict[str, Any]:
    """End-to-end smoke used by `om-ai upgrade sprint1`."""
    q = "Create React login page"
    # Intentionally weak answer to exercise the loop
    weak = "here is login maybe use react somehow"
    from om_ai.core.reasoning.pipeline import run_reasoning_pipeline

    strong = run_reasoning_pipeline(q, retrieve=False).get("markdown") or ""
    weak_report = improve_from_exchange(q, weak, bump=True)
    strong_eval = evaluate_answer(q, strong)
    return {
        "name": "om-upgrade-sprint1",
        "weak_path": weak_report,
        "strong_eval": strong_eval,
        "message": "Improvement loop ran: weak answer → dataset + queue; strong reasoning scored.",
    }
