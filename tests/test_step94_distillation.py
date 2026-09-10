"""STEP 94 — Multi-LLM Teacher Distillation."""
from __future__ import annotations

import json
from pathlib import Path

from om_ai.core.distillation import TeacherManager
from om_ai.core.distillation.quality_ranker import QualityRanker
from om_ai.core.steps import OMRoadmapStack


def test_roadmap_includes_step94():
    status = OMRoadmapStack().status()
    assert status["94_teacher_distillation"] == "complete"
    assert status["93_model_training"] == "complete"
    assert hasattr(OMRoadmapStack(), "distillation")


def test_quality_ranker_rejects_garbage():
    r = QualityRanker().score_one("x", "asdfgh asdfgh lorem ipsum")
    assert r["pass"] is False


def test_teacher_collect_and_save(tmp_path: Path):
    def fake_chat(provider_id, messages, **kwargs):
        task = messages[-1]["content"]
        bodies = {
            "gpt": (
                f"Laravel multi-tenant for: {task}\n"
                "- Tenant isolation via separate schemas\n"
                "- Middleware to resolve tenant\n"
                "- Database strategy and permissions\n"
                "- Queue handling per tenant\n"
                "Also cover auth, cache, and observability."
            ),
            "claude": (
                f"Architecture notes for {task}\n"
                "1. Isolation boundaries\n"
                "2. Middleware + permissions\n"
                "3. Database tenancy patterns\n"
                "4. Queue and audit trails\n"
                "Trade-offs: shared DB vs DB-per-tenant."
            ),
            "gemini": (
                "Short weak reply without structure."
            ),
            "qwen": (
                f"Build plan for {task}\n"
                "* Middleware\n* Database strategy\n* Permissions\n* Queue handling\n"
                "* Security encryption and deployment testing\n"
                "Recommend MVP then harden tenant isolation."
            ),
        }
        return bodies.get(provider_id, "generic answer " * 20), f"{provider_id}-test", provider_id

    from om_ai.core.distillation.llm_harvester import LLMHarvester

    harvester = LLMHarvester(
        teachers=["gpt", "claude", "gemini", "qwen"],
        chat_fn=fake_chat,
        allow_mock=False,
    )
    # provider_ready will fail without keys — force live path by patching ready
    harvester._ready = lambda pid: (True, "ok")  # type: ignore[method-assign]

    manager = TeacherManager(
        teachers=["gpt", "claude", "gemini", "qwen"],
        output_root=tmp_path,
        allow_mock=False,
        harvester=harvester,
    )
    result = manager.collect_and_save(
        "Build a Laravel multi tenant architecture",
        output=tmp_path,
    )
    assert result["saved"] is True
    assert result["ranking"]["best"]["provider"] in {"gpt", "claude", "qwen"}
    assert "isolation" in " ".join(result["comparison"]["common_points"]) or result[
        "comparison"
    ]["common_points"]
    sft = result["dataset"]["sft"]
    assert sft["instruction"].startswith("Build a Laravel")
    assert sft["output"]
    written = result["export"]["written"]
    assert Path(written["sft_task"]).is_file()
    line = Path(written["sft_task"]).read_text(encoding="utf-8").strip().splitlines()[0]
    row = json.loads(line)
    assert row["instruction"]
    assert row["output"]


def test_distill_skips_by_default_on_learn():
    out = OMRoadmapStack().distillation.learn_from_turn("hi", "hello", quality={"score": 0.9})
    assert out.get("skipped") is True
