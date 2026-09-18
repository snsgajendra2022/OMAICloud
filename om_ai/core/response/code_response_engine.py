"""STEP 27 — Code-oriented response formatting."""
from __future__ import annotations

import re
from typing import Any


class CodeResponseEngine:
    def format(
        self,
        answer: str,
        *,
        language: str = "",
        message: str = "",
    ) -> dict[str, Any]:
        text = (answer or "").strip()
        lang = (language or self._detect_lang(message) or "text").strip()
        if "```" in text:
            return {"answer": text, "has_code": True, "language": lang}
        # If answer looks like code without fences, wrap lightly.
        if self._looks_code(text):
            fenced = f"```{lang}\n{text}\n```"
            wrapped = (
                f"Here is a practical snippet:\n\n{fenced}\n\n"
                "Adjust names/paths to match your project."
            )
            return {"answer": wrapped, "has_code": True, "language": lang}
        return {
            "answer": text
            or (
                "Share the target language/file and desired behavior, "
                "and I will provide a concrete snippet."
            ),
            "has_code": False,
            "language": lang,
        }

    def _detect_lang(self, message: str) -> str:
        low = (message or "").lower()
        for key, lang in (
            ("python", "python"),
            ("react", "tsx"),
            ("typescript", "ts"),
            ("javascript", "js"),
            ("sql", "sql"),
            ("bash", "bash"),
        ):
            if key in low:
                return lang
        return ""

    def _looks_code(self, text: str) -> bool:
        if not text:
            return False
        return bool(
            re.search(r"(def |class |function |const |import |from |SELECT )", text)
        )
