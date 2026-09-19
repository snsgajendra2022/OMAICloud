"""macOS / local TTS — free path. Default: Aman (Indian male)."""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Prefer real Indian male companion voice on macOS
_PREFERRED_VOICES = (
    "Aman",
    "Rishi",
    "Daniel",
    "Alex",
    "Moira",
    "Samantha",
)
_HINDI_VOICES = (
    "Aman",   # Hinglish / Latin — keep male companion identity
    "Rishi",
    "Lekha",  # Devanagari fallback if Aman struggles
    "Veena",
)


class SpeechSynthesizer:
    def __init__(self) -> None:
        self._backend = "none"
        self._error: str | None = None
        self._voice: str | None = None
        self._rate = int(os.getenv("OM_COMPANION_TTS_RATE") or "178")
        self._detect()

    def _detect(self) -> None:
        if shutil.which("say"):
            self._backend = "macos_say"
            self._voice = self._pick_macos_voice()
            return
        try:
            import pyttsx3  # noqa: F401

            self._backend = "pyttsx3"
            return
        except Exception as exc:
            self._error = str(exc)
        try:
            from om_ai.voice.text_to_speech import TextToSpeech  # noqa: F401

            self._backend = "om_voice_tts"
        except Exception as exc:
            self._error = f"{self._error}; {exc}"

    def _pick_macos_voice(self) -> str | None:
        forced = (os.getenv("OM_COMPANION_TTS_VOICE") or "").strip()
        if forced:
            return forced
        return self._pick_voice_from(_PREFERRED_VOICES) or "Aman"

    def _pick_voice_from(self, names: tuple[str, ...]) -> str | None:
        try:
            out = subprocess.run(
                ["say", "-v", "?"],
                capture_output=True,
                text=True,
                check=False,
            )
            available = out.stdout or ""
            for name in names:
                # Match voice name at line start (avoid false hits)
                for line in available.splitlines():
                    if line.strip().startswith(name + " ") or line.strip().startswith(name + "\t"):
                        return name
                if re_search_voice(name, available):
                    return name
        except Exception as exc:
            logger.debug("voice probe failed: %s", exc)
        return None

    @property
    def ready(self) -> bool:
        return self._backend != "none"

    def status(self) -> dict[str, Any]:
        return {
            "backend": self._backend,
            "ready": self.ready,
            "error": self._error,
            "voice": self._voice,
            "rate": self._rate,
            "accent": "indian_english",
            "free": True,
        }

    def synthesize(
        self,
        text: str,
        *,
        output_path: str | Path | None = None,
        emotion: str = "calm",
        preplanned: bool = False,
    ) -> dict[str, Any]:
        """
        Render audio. If preplanned=True (or text already has [[rate]]),
        do not re-run human_delivery — TTSProvider already paced it.
        """
        text = (text or "").strip()
        if not text:
            return {"ok": False, "reason": "empty"}

        rate = self._rate
        already = preplanned or "[[rate" in text.lower()
        if not already:
            try:
                from om_ai.core.voice_engine.human_delivery import delivery_plan

                plan = delivery_plan(text, emotion=emotion)
                text = str(plan.get("spoken_tts") or text)
                rate = int(plan.get("rate") or self._rate)
            except Exception:
                pass

        out = Path(output_path) if output_path else Path(tempfile.mkstemp(suffix=".aiff")[1])
        try:
            if self._backend == "macos_say":
                voice = self._voice or "Aman"
                try:
                    from om_ai.core.companion_personality.voice_presence import detect_speech_locale

                    if detect_speech_locale(text) == "hi":
                        # Stay on Aman for Hinglish identity; only switch if Devanagari-heavy
                        if _has_devanagari(text):
                            voice = self._pick_voice_from(_HINDI_VOICES) or voice
                        else:
                            voice = self._pick_voice_from(("Aman", "Rishi")) or voice
                except Exception:
                    pass
                if "[[rate" in text.lower():
                    cmd = ["say", "-o", str(out)]
                else:
                    cmd = ["say", "-o", str(out), "-r", str(rate)]
                if voice:
                    cmd.extend(["-v", voice])
                if out.suffix.lower() == ".wav":
                    cmd.extend(["--data-format=LEI16@22050"])
                cmd.append(text)
                proc = subprocess.run(cmd, check=False, capture_output=True)
                ok = out.exists() and out.stat().st_size > 44
                if not ok and proc.stderr:
                    logger.warning("say failed: %s", proc.stderr[:400])
                return {
                    "ok": ok,
                    "path": str(out),
                    "backend": self._backend,
                    "voice": voice,
                    "rate": rate,
                    "text": text,
                    "free": True,
                }
            if self._backend == "pyttsx3":
                import pyttsx3

                eng = pyttsx3.init()
                eng.setProperty("rate", rate)
                eng.save_to_file(text, str(out.with_suffix(".wav")))
                eng.runAndWait()
                path = out.with_suffix(".wav")
                return {
                    "ok": path.exists(),
                    "path": str(path),
                    "backend": self._backend,
                    "text": text,
                    "free": True,
                }
            if self._backend == "om_voice_tts":
                from om_ai.voice.text_to_speech import TextToSpeech

                result = TextToSpeech().generate(text)
                return {
                    "ok": True,
                    "path": None,
                    "backend": self._backend,
                    "result": result,
                    "text": text,
                    "free": True,
                }
            return {
                "ok": False,
                "reason": "tts_unavailable",
                "text": text,
                "backend": self._backend,
            }
        except Exception as exc:
            logger.warning("TTS failed: %s", exc)
            return {"ok": False, "error": str(exc), "text": text, "backend": self._backend}


def re_search_voice(name: str, available: str) -> bool:
    return f"\n{name} " in f"\n{available}" or available.startswith(f"{name} ")


def _has_devanagari(text: str) -> bool:
    return any("\u0900" <= ch <= "\u097F" for ch in (text or ""))
