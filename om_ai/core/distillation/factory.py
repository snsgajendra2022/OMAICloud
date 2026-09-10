"""Factory helpers for OM distillation engine."""
from __future__ import annotations

import os

from .distillation_engine import DistillationEngine
from .ollama_client import OllamaClient
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
    return TeacherManager(
        teachers=models,
        registry=registry,
        client=client,
        allow_mock=True,
    )


def create_distillation_engine() -> DistillationEngine:
    """Create a ready DistillationEngine with teacher manager wired."""
    return DistillationEngine(teacher_manager=create_teacher_manager())
