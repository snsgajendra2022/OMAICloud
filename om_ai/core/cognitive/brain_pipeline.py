"""OM-1.0 Cognitive Brain — facade over the existing reasoning pipeline.

Do not call ``OMCognitiveBrain.process()`` at import time. Always pass a question:

    OMCognitiveBrain().process("create react native login and dashboard app")
"""
from __future__ import annotations

from typing import Any

from om_ai.cognition.intent_engine import IntentEngine
from om_ai.cognition.task_planner import TaskPlanner
from om_ai.cognition.technology_engine import TechnologyEngine
from om_ai.core.reasoning.reasoning_chain import ReasoningChain
from om_ai.core.response.answer_generator import AnswerGenerator
from om_ai.evaluation.self_checker import SelfEvaluator
from om_ai.understanding.query_kind import is_coding_task, is_greeting, query_kind


class OMCognitiveBrain:
    def __init__(self) -> None:
        self.intent = IntentEngine()
        self.technology = TechnologyEngine()
        self.planner = TaskPlanner()
        self.reasoning = ReasoningChain()
        self.generator = AnswerGenerator()
        self.evaluator = SelfEvaluator()

    def process(self, question: str, knowledge: Any = None) -> dict[str, Any]:
        question = (question or "").strip()
        if not question:
            return {
                "answer": "",
                "user_response": "",
                "developer_response": "",
                "debug": {},
                "intent": {},
                "technology": {},
                "tasks": {"goal": "", "category": "general", "tasks": []},
                "reasoning": {},
                "evaluation": {
                    "approved": False,
                    "score": 0.0,
                    "issues": ["empty question"],
                    "improvement_needed": True,
                },
            }

        kind = query_kind(question)
        intent_result = self.intent.analyze(question)
        technology_result = (
            self.technology.analyze(question) if is_coding_task(question) else {
                "technology": None,
                "category": "unknown",
                "language": None,
                "platform": None,
                "confidence": 0,
            }
        )
        task_result = self.planner.decompose(question)
        if kind in {"greeting", "knowledge"}:
            task_result = {"goal": question, "category": "general", "tasks": []}

        hits: list[str] | None = None
        if kind == "greeting":
            hits = []
        elif isinstance(knowledge, list):
            hits = [str(x).strip() for x in knowledge if str(x).strip()]
        elif isinstance(knowledge, dict):
            text = str(knowledge.get("text") or knowledge.get("answer") or "").strip()
            hits = [text] if text else None
        elif isinstance(knowledge, str) and knowledge.strip():
            hits = [knowledge.strip()]

        from om_ai.core.reasoning.pipeline import run_reasoning_pipeline

        pipeline = run_reasoning_pipeline(
            question,
            knowledge_hits=hits,
            retrieve=not hits and kind != "greeting",
        )
        generated = None
        user_from_pipeline = str(pipeline.get("user_response") or pipeline.get("answer") or "").strip()
        if not user_from_pipeline:
            reasoning_result = self.reasoning.analyze(
                question,
                intent=intent_result,
                technology=technology_result,
                tasks=task_result,
                knowledge=knowledge if isinstance(knowledge, dict) else None,
            )
            generated = self.generator.generate(question, reasoning_result, knowledge)
            if isinstance(generated, dict):
                user_from_pipeline = str(generated.get("answer") or "").strip()
            else:
                user_from_pipeline = str(generated or "").strip()

        evaluation = pipeline.get("evaluation") or self.evaluator.evaluate(
            question,
            user_from_pipeline,
            pipeline.get("technology") or technology_result,
        )
        from om_ai.core.response.response_formatter import ResponseFormatter, response_mode

        formatter = ResponseFormatter()
        payload = {
            "question": question,
            "intent": pipeline.get("intent") or intent_result,
            "technology": pipeline.get("technology") or technology_result,
            "tasks": pipeline.get("debug", {}).get("tasks") or task_result,
            "reasoning": pipeline,
            "answer": str(pipeline.get("solution") or user_from_pipeline),
            "evaluation": evaluation,
            "understanding": pipeline.get("understanding") or question,
            "plan": pipeline.get("plan") or task_result.get("tasks") or [],
            "architecture": pipeline.get("architecture") or [],
            "markdown": pipeline.get("markdown") or "",
        }
        user_response = str(pipeline.get("user_response") or "").strip() or formatter.format_user_response(payload)
        if is_greeting(question) and "agents:" in user_response.lower():
            user_response = formatter.format_user_response({"question": question})
        developer_response = str(
            pipeline.get("developer_response") or pipeline.get("markdown") or ""
        ).strip() or formatter.format_developer_response(payload)
        visible = developer_response if response_mode() == "developer" else user_response
        debug = pipeline.get("debug") or {
            "intent": payload["intent"],
            "technology": payload["technology"],
            "evaluation": evaluation,
            "markdown": developer_response,
        }
        return {
            "answer": visible,
            "user_response": user_response,
            "developer_response": developer_response,
            "debug": debug,
            "intent": payload["intent"],
            "technology": payload["technology"],
            "tasks": task_result,
            "reasoning": pipeline,
            "evaluation": evaluation,
        }
