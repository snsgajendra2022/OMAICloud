"""
OM AI Universal Language Manager

Main controller for language intelligence.
"""
from __future__ import annotations

from typing import Any

from .detector import LanguageDetector
from .analyzer import LanguageAnalyzer
from .response_language import ResponseLanguageController
from .translator import LanguageTranslator


class LanguageManager:
    def __init__(self) -> None:
        self.detector = LanguageDetector()
        self.analyzer = LanguageAnalyzer()
        self.response = ResponseLanguageController()
        self.translator = LanguageTranslator()

    def process(self, text: str) -> dict[str, Any]:
        language = self.detector.detect(text)
        analysis = self.analyzer.analyze(text)
        response_language = self.response.select_language(language)
        instruction = self.response.build_instruction(response_language)
        meaning: dict[str, Any] = {}
        try:
            from .meaning import extract_meaning

            meaning = extract_meaning(text, language=language)
        except Exception:
            meaning = {}
        return {
            "input": text,
            "language": language,
            "analysis": analysis,
            "response_language": response_language,
            "instruction": instruction,
            "meaning": meaning,
        }

    def ensure_response_language(
        self,
        answer: str,
        *,
        target_language: str,
        user_text: str = "",
    ) -> dict[str, Any]:
        """Stage: Response Language Check — align final answer to user language."""
        return self.response.ensure(
            answer,
            target_language=target_language,
            user_text=user_text,
            translator=self.translator,
        )
