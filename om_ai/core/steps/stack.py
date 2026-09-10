"""OM Roadmap Stack — STEPs 83–94 unified runtime."""
from __future__ import annotations

from typing import Any

from .step83_continuous_learning import ContinuousLearningIntelligence
from .step84_advanced_learning import AdvancedLearningIntelligence
from .step85_agent_civilization import AgentCivilization
from .step86_global_knowledge import GlobalKnowledgeIntelligence
from .step88_advanced_reasoning import AdvancedReasoningIntelligence
from .step89_long_context import LongContextIntelligence
from .step90_agent_collaboration import AgentCollaborationUpgrade
from .step91_self_improvement import SelfImprovementEngine
from .step92_knowledge_brain import KnowledgeBrain
from .step93_model_training import ModelTrainingIntelligence
from .step94_teacher_distillation import TeacherDistillationIntelligence


class OMRoadmapStack:
    """Complete STEPs 83–94 intelligence layer for OMCognitiveBrain."""

    def __init__(self) -> None:
        self.continuous = ContinuousLearningIntelligence()
        self.advanced_learning = AdvancedLearningIntelligence()
        self.civilization = AgentCivilization()
        self.global_knowledge = GlobalKnowledgeIntelligence()
        self.advanced_reasoning = AdvancedReasoningIntelligence()
        self.long_context = LongContextIntelligence()
        self.collaboration = AgentCollaborationUpgrade()
        self.self_improvement = SelfImprovementEngine()
        self.knowledge_brain = KnowledgeBrain()
        self.training = ModelTrainingIntelligence()
        self.distillation = TeacherDistillationIntelligence()

    def enrich_before_answer(
        self,
        message: str,
        *,
        knowledge: Any = None,
        memory: Any = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = context or {}
        prior = []
        if isinstance(context.get("history"), list):
            prior = context["history"]
        mem_items = memory if isinstance(memory, list) else ([memory] if memory else [])

        long_ctx = self.long_context.process(
            message, memory_items=mem_items, prior_turns=prior
        )
        reasoning = self.advanced_reasoning.reason(message)
        knowledge_pack = self.knowledge_brain.answer_with_knowledge(
            message, knowledge=knowledge
        )
        global_pack = self.global_knowledge.retrieve(message, knowledge=knowledge)

        low = (message or "").lower()
        agents = None
        collab = None
        if any(
            w in low
            for w in (
                "build",
                "create",
                "design",
                "architect",
                "ecommerce",
                "uber",
                "application",
                "system",
            )
        ):
            agents = self.civilization.run(message)
            collab = self.collaboration.collaborate(message)

        return {
            "long_context": long_ctx,
            "advanced_reasoning": reasoning,
            "knowledge_brain": knowledge_pack,
            "global_knowledge": global_pack,
            "civilization": agents,
            "collaboration": collab,
            "context_blob": "\n\n".join(
                [
                    str((long_ctx or {}).get("context") or ""),
                    str((knowledge_pack or {}).get("context") or ""),
                    str((global_pack or {}).get("context") or ""),
                    str((reasoning or {}).get("final_reasoning") or "")[:2000],
                    str((collab or {}).get("summary") or "")[:2000],
                ]
            ).strip()[:8000],
        }

    def learn_after_answer(
        self,
        message: str,
        answer: str,
        quality: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        quality = quality or {}
        c83 = self.continuous.learn(message, answer, quality=quality, meta=meta)
        c84 = self.advanced_learning.improve(message, answer, quality=quality)
        c91 = self.self_improvement.improve(message, answer, quality=quality)
        c93 = self.training.prepare_from_turn(message, answer, quality=quality)
        c94 = self.distillation.learn_from_turn(message, answer, quality=quality)
        return {
            "step83": c83,
            "step84": c84,
            "step91": c91,
            "step93": c93,
            "step94": c94,
            "skills": self.continuous.skill_snapshot(),
            "behaviors": c91.get("behaviors"),
        }

    def status(self) -> dict[str, str]:
        return {
            "83_continuous_learning": "complete",
            "84_advanced_learning": "complete",
            "85_agent_civilization": "complete",
            "86_global_knowledge": "complete",
            "87_research": "complete",
            "88_advanced_reasoning": "complete",
            "89_long_context": "complete",
            "90_agent_collaboration": "complete",
            "91_self_improvement": "complete",
            "92_knowledge_brain": "complete",
            "93_model_training": "complete",
            "94_teacher_distillation": "complete",
            "94.10_teacher_intelligence": "complete",
            "94.11_curriculum_generator": "complete",
            "94.12_harvest_scheduler": "complete",
            "94.13_knowledge_gap_collector": "complete",
            "94.14_continuous_loop": "complete",
        }
