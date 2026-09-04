"""
OM AI Response Language Controller

Controls / verifies final answer language.
"""
from __future__ import annotations

import re
from typing import Any


_LANG_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "ar": "Arabic",
    "gu": "Gujarati",
    "ta": "Tamil",
    "te": "Telugu",
    "zh": "Chinese",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
}


class ResponseLanguageController:
    def select_language(self, detected_language: str) -> str:
        lang = (detected_language or "en").strip().lower() or "en"
        if lang in {"unknown", "und"}:
            return "en"
        return lang

    def build_instruction(self, language: str) -> str:
        name = _LANG_NAMES.get(language, language)
        return (
            f"Generate the response in {name} ({language}). "
            "Keep a natural style. Match the user's language. "
            "Do not switch languages unless asked."
        )

    def _script_ok(self, text: str, language: str) -> bool:
        t = text or ""
        if language == "hi":
            return bool(re.search(r"[\u0900-\u097F]", t)) or not re.search(r"[A-Za-z]{12,}", t)
        if language == "ar":
            return bool(re.search(r"[\u0600-\u06FF]", t))
        if language == "zh":
            return bool(re.search(r"[\u4E00-\u9FFF]", t))
        if language == "en":
            # Prefer Latin; allow code fences mixed with English
            return True
        return True

    def ensure(
        self,
        answer: str,
        *,
        target_language: str,
        user_text: str = "",
        translator: Any = None,
    ) -> dict[str, Any]:
        ans = (answer or "").strip()
        target = self.select_language(target_language)
        ok = self._script_ok(ans, target)
        fixed = ans
        status = "ok"
        if not ok and translator is not None and target != "en":
            try:
                out = translator.translate(ans, "en", target)
                if isinstance(out, dict):
                    fixed = str(out.get("translated") or ans)
                    status = str(out.get("status") or "checked")
                elif isinstance(out, str) and out.strip():
                    fixed = out.strip()
                    status = "translated"
            except Exception:
                status = "check_failed"
        # Always attach instruction reminder is handled upstream; here only gate text
        if not fixed:
            fixed = ans
        return {
            "ok": ok,
            "target_language": target,
            "status": status,
            "answer": fixed,
            "instruction": self.build_instruction(target),
        }
