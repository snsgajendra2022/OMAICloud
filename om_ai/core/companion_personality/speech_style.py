"""Transform brain text into natural spoken form for TTS."""
from __future__ import annotations

import re
from typing import Any


_ROBOTIC = [
    (re.compile(r"(?i)^as an ai[, ]*"), ""),
    (re.compile(r"(?i)^certainly[,!]?\s*i('d| would) be happy to\s*"), ""),
    (re.compile(r"(?i)^sure[,!]?\s*i can help (you )?with that[.!]?\s*"), ""),
    (re.compile(r"(?i)how can i (assist|help) you( today)?\??"), ""),
    (re.compile(r"(?i)is there anything else i can help you with\??"), ""),
    (re.compile(r"(?i)please let me know if you (need|have) .*"), ""),
    (re.compile(r"(?i)i want to help\s*[—\-–,]?\s*could you rephrase.*"), ""),
    (re.compile(r"(?i)please rephrase.*(short|plain).*"), ""),
]


class SpeechStyle:
    def strip_markdown(self, text: str) -> str:
        t = text or ""
        t = re.sub(r"```[\s\S]*?```", " ", t)
        t = re.sub(r"`([^`]+)`", r"\1", t)
        t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
        t = re.sub(r"[*_#>]+", " ", t)
        t = re.sub(r"(?m)^\s*[-•]\s+", "", t)
        t = re.sub(r"(?m)^\s*\d+[.)]\s+", "", t)
        t = re.sub(r"\s+", " ", t)
        return t.strip()

    def transform(
        self,
        response: str,
        locale: str,
        emotion: str,
        personality: dict[str, Any] | None = None,
    ) -> str:
        text = self.strip_markdown((response or "").strip())
        for pat, repl in _ROBOTIC:
            text = pat.sub(repl, text).strip()

        text = text.replace(" ; ", ". ")
        if locale != "hi":
            text = text.replace(" — ", ". ").replace(" - ", ". ")

        if locale == "hi":
            text = self.hinglish_style(text, emotion=emotion)
        else:
            text = self.english_style(text, emotion=emotion)

        return text.strip()

    def english_style(self, text: str, *, emotion: str = "neutral") -> str:
        words = text.split()
        if len(words) > 45:
            sentences = re.split(r"(?<=[.!?])\s+", text)
            text = " ".join(s.strip() for s in sentences[:3] if s.strip())
        # Soft cadence hint only — never invent a new reply
        if emotion in {"tired", "sad", "stress"} and text and not text.endswith(("?", "…")):
            pass
        return text

    def hinglish_style(self, text: str, *, emotion: str = "neutral") -> str:
        words = text.split()
        if len(words) > 50:
            sentences = re.split(r"(?<=[.!?।])\s+", text)
            text = " ".join(s.strip() for s in sentences[:3] if s.strip())
        return text

    def pace_for_tts(self, spoken: str) -> str:
        """Light conversational cadence — heavy pauses sound robotic, not human."""
        try:
            from om_ai.core.voice_engine.human_delivery import apply_human_prosody

            return apply_human_prosody(spoken, emotion="calm")
        except Exception:
            t = (spoken or "").strip()
            if "[[slnc" in t.lower():
                return t
            # Keep ellipsis intact — never turn "..." into ". . ."
            t = t.replace("…", "...")
            t = re.sub(r"\.{3,}", "«ELLIP»", t)
            t = re.sub(r"([.!?])\s+", r"\1 [[slnc 180]] ", t)
            t = re.sub(r"([,;:])\s+", r"\1 [[slnc 90]] ", t)
            t = t.replace("«ELLIP»", " [[slnc 200]] ")
            return re.sub(r"\s+", " ", t).strip()
