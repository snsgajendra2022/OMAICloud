"""Verify STEPs 83–93 roadmap stack is complete and wired."""
from __future__ import annotations

from om_ai.core.steps import OMRoadmapStack
from om_ai.core.cognitive.brain_pipeline import OMCognitiveBrain


def test_roadmap_status_complete():
    status = OMRoadmapStack().status()
    assert status["83_continuous_learning"] == "complete"
    assert status["87_research"] == "complete"
    assert status["93_model_training"] == "complete"
    assert len(status) == 11


def test_brain_has_roadmap():
    brain = OMCognitiveBrain()
    assert hasattr(brain, "roadmap")
    out = brain.generate(
        "Design Uber architecture",
        native_chat=lambda m: "Riders, drivers, matching, payments.",
    )
    assert out["status"] == "ok"
    assert "roadmap_enrich" in out["stages"]
    assert (out.get("meta") or {}).get("reasoning", {}).get("mode") == "architecture"


def test_refuse_random_words():
    out = OMCognitiveBrain().generate("generate random words")
    assert "will not output" in out["answer"].lower()
