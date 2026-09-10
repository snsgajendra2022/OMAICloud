"""TeacherManager — orchestrate Multi-LLM harvest → train export."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .answer_comparator import AnswerComparator
from .dataset_builder import DatasetBuilder
from .distillation_state import DistillationState
from .knowledge_collector import KnowledgeCollector
from .llm_harvester import DEFAULT_TEACHERS, LLMHarvester
from .quality_ranker import QualityRanker
from .training_exporter import TrainingExporter
from .models import TeacherResponse


class TeacherManager:
    """
    External Intelligence Sources
      → Knowledge Extraction (clean/verify)
      → Compare + Rank
      → OM training JSONL (SFT/DPO)
    """

    def __init__(
        self,
        *,
        teachers: list[str] | tuple[str, ...] | None = None,
        output_root: Path | str | None = None,
        stored_keys: dict[str, str] | None = None,
        allow_mock: bool | None = None,
        harvester: LLMHarvester | None = None,
        registry=None,
        client=None,
    ) -> None:
        self.state = DistillationState(output_root)
        self.harvester = harvester or LLMHarvester(
            teachers=teachers or DEFAULT_TEACHERS,
            stored_keys=stored_keys,
            allow_mock=allow_mock,
        )
        self.collector = KnowledgeCollector(self.state)
        self.comparator = AnswerComparator()
        self.ranker = QualityRanker()
        self.builder = DatasetBuilder()
        self.exporter = TrainingExporter(self.state)
        if client is None:
            try:
                from .ollama_client import OllamaClient

                client = OllamaClient()
            except Exception:
                client = None
        if registry is None and client is not None:
            try:
                from .teacher_registry import TeacherRegistry

                registry = TeacherRegistry(client)
            except Exception:
                registry = None
        self.registry = registry
        self.client = client

    def collect(
        self,
        task: str,
        *,
        teachers: list[str] | None = None,
    ) -> dict[str, Any]:
        """Harvest → clean → verify → compare → rank → build training pack."""
        task = (task or "").strip()
        if not task:
            raise ValueError("task is required")
        run_id = self.state.new_run_id(task)

        harvest = self.harvester.harvest(task, teachers=teachers)
        cleaned = self.collector.process_harvest(harvest, run_id=run_id)
        comparison = self.comparator.compare(task, cleaned.get("responses") or [])
        ranking = self.ranker.rank(
            task,
            cleaned.get("responses") or [],
            common_points=comparison.get("common_points") or [],
        )
        pack = self.builder.build_pack(task, ranking, comparison, run_id=run_id)

        return {
            "step": 94,
            "run_id": run_id,
            "task": task,
            "harvest": {
                "ok_count": cleaned.get("ok_count"),
                "live_count": cleaned.get("live_count"),
                "mock_count": cleaned.get("mock_count"),
                "raw_path": cleaned.get("raw_path"),
                "clean_path": cleaned.get("clean_path"),
            },
            "comparison": comparison,
            "ranking": {
                "best": ranking.get("best"),
                "pass_count": ranking.get("pass_count"),
                "ranked": [
                    {
                        "provider": r.get("provider"),
                        "score": r.get("score"),
                        "pass": r.get("pass"),
                    }
                    for r in (ranking.get("ranked") or [])
                ],
            },
            "dataset": pack,
            "pipeline": [
                "raw_knowledge",
                "cleaning",
                "verification",
                "ranking",
                "training_dataset",
            ],
        }

    def save(
        self,
        result: dict[str, Any],
        *,
        output: Path | str | None = None,
        also_training_buffer: bool = True,
    ) -> dict[str, Any]:
        pack = result.get("dataset") or {}
        if not pack.get("run_id"):
            pack = {
                **pack,
                "run_id": result.get("run_id"),
                "task": result.get("task"),
            }
        export_info = self.exporter.export(
            pack,
            output_dir=output or self.state.root,
            also_training_buffer=also_training_buffer,
        )
        return {
            **result,
            "saved": True,
            "export": export_info,
            "output": str(output or self.state.root),
        }

    def collect_and_save(
        self,
        task: str,
        *,
        output: Path | str | None = None,
        teachers: list[str] | None = None,
    ) -> dict[str, Any]:
        result = self.collect(task, teachers=teachers)
        return self.save(result, output=output)

    def ask_teachers(
        self,
        question: str
    ):
        responses = []
        if self.registry is None or self.client is None:
            return responses

        teachers = (
            self.registry
            .get_ready_models()
        )


        for teacher in teachers:


            try:

                result = (

                    self.client
                    .generate(

                        model=teacher.name,

                        prompt=question

                    )

                )


                responses.append(

                    TeacherResponse(

                        question=question,

                        teacher=teacher.name,

                        response=result["text"],

                        latency_ms=
                            result["latency_ms"],

                        metadata=
                            result["metadata"]

                    )

                )


            except Exception as error:


                responses.append(

                    TeacherResponse(

                        question=question,

                        teacher=teacher.name,

                        response="",

                        status="failed",

                        metadata={
                            "error":
                            str(error)
                        }

                    )

                )


        return responses