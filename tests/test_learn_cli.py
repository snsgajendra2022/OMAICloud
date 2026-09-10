"""om-ai learn command layer (argparse)."""
from __future__ import annotations

from pathlib import Path

from om_ai.core.learning import ImprovementCycle, LearningScheduler, TrainingQueue


def test_learn_start_with_topic(tmp_path: Path):
    cycle = ImprovementCycle(
        scheduler=LearningScheduler(tmp_path / "sched"),
        training_queue=TrainingQueue(tmp_path / "tq"),
    )

    def fake_harvest(q: str):
        return {
            "run_id": "r1",
            "dataset": {
                "run_id": "r1",
                "sft": {
                    "instruction": q,
                    "output": "answer about " + q,
                    "messages": [
                        {"role": "user", "content": q},
                        {"role": "assistant", "content": "answer"},
                    ],
                    "meta": {"score": 0.8},
                },
            },
            "export": {"exported": 1},
        }

    cycle.worker.harvest_fn = fake_harvest
    out = cycle.start(topic="React", count=2, max_items=2, cycles=1)
    assert out["command"] == "learn.start"
    assert out["planned"]["seeded"] == 2
    assert out["cycles"][0]["ran"] >= 1
    assert cycle.training_queue.pending_count() >= 1


def test_learn_status():
    st = ImprovementCycle().status()
    assert "scheduler" in st
    assert "training_queue" in st
    assert st["flow"][0] == "knowledge_gaps"
