"""TeacherManager — orchestrate Multi-LLM harvest → train export."""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        parallelism: int | None = None,
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
        if parallelism is None:
            parallelism = int(os.getenv("OM_TEACHER_PARALLELISM", "2") or 2)
        self.parallelism = max(1, int(parallelism))
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

    def _harvest_via_ollama(
        self,
        task: str,
        *,
        teachers: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """Collect live answers from local Ollama teachers when installed."""
        if self.client is None or self.registry is None:
            return None
        try:
            installed = set(self.registry.installed_models() or [])
        except Exception:
            installed = set()
        if not installed:
            return None

        wanted = [t.strip() for t in (teachers or list(self.harvester.teachers) or []) if t and str(t).strip()]
        if not wanted:
            wanted = list(getattr(self.registry, "configured_models", None) or [])
        ready_names = [n for n in wanted if n in installed]
        if not ready_names:
            # Use any configured teacher that is installed
            ready_names = [
                n
                for n in (getattr(self.registry, "configured_models", None) or [])
                if n in installed
            ]
        if not ready_names:
            ready_names = sorted(installed)[:4]
        if not ready_names:
            return None

        from .models import TeacherModel

        teacher_objs = [TeacherModel(name=n, available=True) for n in ready_names]
        workers = min(self.parallelism, len(teacher_objs))
        rows: list[TeacherResponse] = []
        if workers <= 1 or len(teacher_objs) == 1:
            rows = [self._ask_one(t, task) for t in teacher_objs]
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(self._ask_one, t, task): t for t in teacher_objs}
                for fut in as_completed(futures):
                    rows.append(fut.result())
            order = {n: i for i, n in enumerate(ready_names)}
            rows.sort(key=lambda r: order.get(r.teacher, 999))

        responses: list[dict[str, Any]] = []
        for r in rows:
            ok = (r.status or "success") == "success" and bool((r.response or "").strip())
            responses.append(
                {
                    "provider": r.teacher,
                    "ok": ok,
                    "text": (r.response or "").strip(),
                    "model": r.teacher,
                    "vendor": "ollama",
                    "source": "ollama" if ok else "failed",
                    "error": "" if ok else str((r.metadata or {}).get("error") or r.status or "failed"),
                    "latency_ms": r.latency_ms,
                }
            )
        live = sum(1 for x in responses if x.get("ok") and x.get("source") == "ollama")
        if live <= 0:
            return None
        return {
            "task": task,
            "teachers": ready_names,
            "responses": responses,
            "ok_count": live,
            "live_count": live,
            "mock_count": 0,
        }

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

        # Prefer real local Ollama teachers; only then API/mock harvester.
        harvest = self._harvest_via_ollama(task, teachers=teachers)
        if harvest is None:
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
            "parallelism": self.parallelism,
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

    def _ask_one(self, teacher: Any, question: str) -> TeacherResponse:
        try:
            result = self.client.generate(model=teacher.name, prompt=question) or {}
            text = str(result.get("response") or result.get("text") or "").strip()
            if result.get("status") != "success" or not text:
                return TeacherResponse(
                    question=question,
                    teacher=teacher.name,
                    response="",
                    status="failed",
                    metadata={
                        "error": result.get("error") or "empty_or_failed",
                        "ollama": result.get("metadata") or {},
                    },
                )
            return TeacherResponse(
                question=question,
                teacher=teacher.name,
                response=text,
                latency_ms=float(result.get("latency_ms") or 0),
                metadata=result.get("metadata") or {},
            )
        except Exception as error:
            return TeacherResponse(
                question=question,
                teacher=teacher.name,
                response="",
                status="failed",
                metadata={"error": str(error)},
            )

    def ask_teachers(
        self,
        question: str,
    ):
        """Ask Ollama teachers in parallel, or fall back to harvester mocks."""

        def _from_harvest() -> list[TeacherResponse]:
            out: list[TeacherResponse] = []
            harvest = self.harvester.harvest(question)
            for row in harvest.get("responses") or []:
                if not row.get("ok"):
                    continue
                out.append(
                    TeacherResponse(
                        question=question,
                        teacher=str(row.get("provider") or "unknown"),
                        response=str(row.get("text") or ""),
                        latency_ms=0.0,
                        metadata={"source": row.get("source") or "harvester"},
                    )
                )
            return out

        if self.registry is None or self.client is None:
            return _from_harvest()

        try:
            teachers = self.registry.get_ready_models()
        except Exception:
            teachers = []

        if not teachers:
            return _from_harvest()

        # Keep/improve parallelism — concurrent teacher queries.
        workers = min(self.parallelism, len(teachers))
        if workers <= 1 or len(teachers) == 1:
            return [self._ask_one(t, question) for t in teachers]

        responses: list[TeacherResponse] = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(self._ask_one, t, question): t for t in teachers}
            for fut in as_completed(futures):
                responses.append(fut.result())
        order = {getattr(t, "name", str(t)): i for i, t in enumerate(teachers)}
        responses.sort(key=lambda r: order.get(r.teacher, 999))
        return responses
