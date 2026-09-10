"""STEPs 94.10–94.14 distillation extensions."""
from __future__ import annotations

from pathlib import Path

from om_ai.core.distillation import (
    AutonomousHarvestScheduler,
    ContinuousDistillationLoop,
    CurriculumGenerator,
    KnowledgeGapCollector,
    TeacherIntelligence,
    create_continuous_loop,
)
from om_ai.core.steps import OMRoadmapStack


def test_roadmap_marks_94_substeps():
    status = OMRoadmapStack().status()
    assert status["94.10_teacher_intelligence"] == "complete"
    assert status["94.14_continuous_loop"] == "complete"


def test_teacher_intelligence_records(tmp_path: Path):
    intel = TeacherIntelligence(tmp_path)
    ranking = {
        "best": {"provider": "gpt", "score": 0.8, "pass": True},
        "pass_count": 2,
        "ranked": [
            {"provider": "gpt", "score": 0.8, "pass": True},
            {"provider": "claude", "score": 0.6, "pass": True},
        ],
    }
    out = intel.record("Build a Laravel multi tenant architecture", ranking)
    assert out["domain"] in {"software", "security", "architecture", "data"}
    recs = intel.recommend_teachers("Laravel tenant isolation")
    assert recs
    assert intel.profile("gpt")["wins"] >= 1


def test_curriculum_and_scheduler(tmp_path: Path):
    cur = CurriculumGenerator(tmp_path / "cur")
    pack = cur.generate("Kubernetes", domain="devops", count=6)
    assert pack["count"] == 6
    assert Path(pack["path"]).is_file()

    sched = AutonomousHarvestScheduler(tmp_path / "sched")
    jobs = sched.enqueue_many(pack["questions"], source="test")
    assert len(jobs) == 6
    assert len(sched.pending()) == 6

    def fake_harvest(q: str):
        return {"ok": True, "question": q, "ranking": {"best": {"provider": "mock", "score": 0.7}, "pass_count": 1, "ranked": [{"provider": "mock", "score": 0.7, "pass": True}]}}

    ran = sched.run_once(fake_harvest, limit=2)
    assert ran["ran"] == 2
    assert ran["pending"] == 4


def test_gap_collector_and_loop(tmp_path: Path):
    gaps = KnowledgeGapCollector(tmp_path / "gaps")
    assert gaps.collect_from_turn("What is React?", "I don't know", {"score": 0.1})
    gaps.collect_explicit("multi tenant laravel")
    top = gaps.top_gaps(limit=5)
    assert top

    harvested = []

    def harvest(q: str):
        harvested.append(q)
        return {
            "ranking": {
                "best": {"provider": "gpt", "score": 0.75, "pass": True},
                "pass_count": 1,
                "ranked": [{"provider": "gpt", "score": 0.75, "pass": True}],
            }
        }

    loop = ContinuousDistillationLoop(
        gaps=gaps,
        curriculum=CurriculumGenerator(tmp_path / "cur"),
        scheduler=AutonomousHarvestScheduler(tmp_path / "sched"),
        teacher_intel=TeacherIntelligence(tmp_path / "intel"),
        harvest_fn=harvest,
    )
    planned = loop.plan_from_gaps(gap_limit=3, per_gap=1)
    assert planned["queued"] >= 1
    cycle = loop.run_cycle(max_items=2, auto_plan_gaps=False)
    assert cycle["harvest"]["ran"] >= 1
    assert harvested


def test_factory_continuous_loop():
    loop = create_continuous_loop()
    assert loop.harvest_fn is not None
    st = loop.status()
    assert st["step"] == "94.14"
