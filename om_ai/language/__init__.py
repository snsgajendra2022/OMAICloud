"""
OM AI Universal Language Intelligence
"""
from .detector import LanguageDetector
from .analyzer import LanguageAnalyzer
from .translator import LanguageTranslator
from .response_language import ResponseLanguageController
from .manager import LanguageManager
from .meaning import MultilingualKnowledge, extract_meaning

__all__ = [
    "LanguageDetector",
    "LanguageAnalyzer",
    "LanguageTranslator",
    "ResponseLanguageController",
    "LanguageManager",
    "MultilingualKnowledge",
    "extract_meaning",
]
