from __future__ import annotations
from typing import Any

from .hinglish_parser import HinglishParser
from .language_detector import LanguageDetector
from .multilingual_context import MultilingualContext
from .translation_engine import TranslationEngine

_RT = None

class LanguageIntelligence:
    def __init__(self) -> None:
        self.detector = LanguageDetector()
        self.parser = HinglishParser()
        self.context = MultilingualContext()
        self.translator = TranslationEngine()

    def status(self) -> dict[str, Any]:
        return {"ready": True, "name": "Language Intelligence", "mix_support": ["en", "hi", "hi-en"]}

    def understand(self, text: str) -> dict[str, Any]:
        detected = self.detector.detect(text)
        parsed = self.parser.parse(text)
        locale = self.context.reply_locale(detected)
        normalized = self.translator.normalize_for_planner(text, parsed)
        return {
            "detected": detected,
            "locale": locale,
            "parsed": parsed,
            "normalized": normalized,
            "intent": parsed.get("intent"),
            "slots": parsed.get("slots") or {},
            "confidence": float(parsed.get("confidence") or 0),
        }


def get_language_intelligence() -> LanguageIntelligence:
    global _RT
    if _RT is None:
        _RT = LanguageIntelligence()
    return _RT
