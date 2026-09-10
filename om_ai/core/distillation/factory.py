"""Factory helpers for OM distillation engine + STEP 94.10–94.14 stack."""
from __future__ import annotations

import os
from typing import Any

from .continuous_loop import ContinuousDistillationLoop
from .curriculum_generator import CurriculumGenerator
from .distillation_engine import DistillationEngine
from .harvest_scheduler import AutonomousHarvestScheduler
from .knowledge_gap_collector import KnowledgeGapCollector
from .ollama_client import OllamaClient
from .teacher_intelligence import TeacherIntelligence
from .teacher_manager import TeacherManager
from .teacher_registry import TeacherRegistry


def create_teacher_manager() -> TeacherManager:
    """Build TeacherManager from env (Ollama URL + teacher model list)."""
    ollama_url = os.getenv("OM_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    models_raw = os.getenv(
        "OM_TEACHER_MODELS",
        "qwen3:14b,deepseek-r1:14b,mistral:latest",
    )
    models = [x.strip() for x in models_raw.split(",") if x.strip()]
    timeout = int(os.getenv("OM_TEACHER_TIMEOUT", "180"))

    client = OllamaClient(base_url=ollama_url, timeout=timeout)
    registry = TeacherRegistry(client, models)
    parallelism = int(os.getenv("OM_TEACHER_PARALLELISM", "2") or 2)
    return TeacherManager(
        teachers=models,
        registry=registry,
        client=client,
        allow_mock=True,
        parallelism=parallelism,
    )


def create_distillation_engine() -> DistillationEngine:
    """Create a ready DistillationEngine with teacher manager wired."""
    return DistillationEngine(teacher_manager=create_teacher_manager())


def create_continuous_loop(
    *,
    harvest_fn=None,
    use_manager_harvest: bool = True,
) -> ContinuousDistillationLoop:
    """STEP 94.10–94.14 stack with optional harvest function."""
    manager = create_teacher_manager()
    intel = TeacherIntelligence()
    gaps = KnowledgeGapCollector()
    curriculum = CurriculumGenerator()
    scheduler = AutonomousHarvestScheduler()

    fn = harvest_fn
    if fn is None and use_manager_harvest:

        def fn(question: str) -> dict[str, Any]:
            result = manager.collect_and_save(question)
            ranking = (result.get("ranking") or {})
            intel.record(question, ranking)
            if int(ranking.get("pass_count") or 0) == 0:
                gaps.collect_from_ranking(question, ranking)
            return result

    loop = ContinuousDistillationLoop(
        gaps=gaps,
        curriculum=curriculum,
        scheduler=scheduler,
        teacher_intel=intel,
        harvest_fn=fn,
    )
    return loop
