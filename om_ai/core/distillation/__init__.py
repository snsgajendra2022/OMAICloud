"""OM Multi-LLM Teacher Distillation — STEP 94.

Harvest answers from connected external LLMs (GPT/Claude/Gemini/Qwen/…),
clean → verify → rank, then export SFT/DPO training data for OM.

This uses legal API outputs only — never private model weights.
"""
from __future__ import annotations

from .answer_comparator import AnswerComparator
from .dataset_builder import DatasetBuilder
from .distillation_state import DistillationState
from .knowledge_collector import KnowledgeCollector
from .llm_harvester import LLMHarvester
from .quality_ranker import QualityRanker
from .teacher_manager import TeacherManager
from .training_exporter import TrainingExporter
from .config import DistillationConfig
from .response_normalizer import ResponseNormalizer
from .quality_evaluator import QualityEvaluator
from .agreement_engine import AgreementEngine
from .contradiction_detector import ContradictionDetector
from .answer_synthesizer import AnswerSynthesizer
from .models import (
    TeacherModel,
    TeacherResponse,
    DistillationResult,
)
from .ollama_client import OllamaClient

from .teacher_registry import TeacherRegistry
from .knowledge_extractor import (
    KnowledgeExtractor,
    KnowledgeItem,
)

from .knowledge_distiller import (
    KnowledgeDistiller,
)

from .knowledge_writer import (
    KnowledgeWriter,
)

from .sft_builder import SFTBuilder

from .preference_builder import PreferenceBuilder

from .evaluation_builder import EvaluationBuilder
from .progress_tracker import ProgressTracker

from .checkpoint_manager import CheckpointManager

from .provenance_manager import ProvenanceManager

from .harvest_engine import HarvestEngine
from .distillation_engine import (
    DistillationEngine,
)
from .factory import (
    create_distillation_engine,
    create_teacher_manager,
)

__all__ = [
    "DistillationEngine",
    "create_distillation_engine",
    "create_teacher_manager",
    "AnswerComparator",
    "DatasetBuilder",
    "SFTBuilder",
    "PreferenceBuilder",
    "EvaluationBuilder",
    "DistillationState",
    "KnowledgeCollector",
    "LLMHarvester",
    "QualityRanker",
    "TeacherManager",
    "TrainingExporter",
    "DistillationConfig",
    "TeacherModel",
    "TeacherResponse",
    "DistillationResult",
    "OllamaClient",
    "TeacherRegistry",
    "ResponseNormalizer",
    "QualityEvaluator",
    "AgreementEngine",
    "ContradictionDetector",
    "AnswerSynthesizer",
    "KnowledgeExtractor",
    "KnowledgeItem",
    "KnowledgeDistiller",
    "KnowledgeWriter",
    "ProgressTracker",
    "CheckpointManager",
    "ProvenanceManager",
    "HarvestEngine",
]

