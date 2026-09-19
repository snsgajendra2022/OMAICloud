from __future__ import annotations
from typing import Any
from .conversation_analyzer import ConversationAnalyzer
from .improvement_memory import ImprovementMemory
from .mistake_detector import MistakeDetector
from .quality_score import QualityScore

_RT = None

class SelfImprovementRuntime:
    def __init__(self) -> None:
        self.analyzer = ConversationAnalyzer()
        self.mistakes = MistakeDetector()
        self.quality = QualityScore()
        self.memory = ImprovementMemory()

    def status(self) -> dict[str, Any]:
        return {"ready": True, "step": 56, "name": "Self Improvement Engine"}

    def evaluate(self, user: str, answer: str) -> dict[str, Any]:
        analysis = self.analyzer.analyze(user, answer)
        miss = self.mistakes.detect(analysis)
        score = self.quality.score(analysis)
        event = {"user": user[:200], "issues": miss, "score": score}
        if miss:
            self.memory.log(event)
        return {"score": score, "issues": miss, "ok": score >= 0.7, "learning_event": bool(miss)}


def get_self_improvement() -> SelfImprovementRuntime:
    global _RT
    if _RT is None:
        _RT = SelfImprovementRuntime()
    return _RT
