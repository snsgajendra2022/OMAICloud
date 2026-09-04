"""
STEP 91 — OM Voice Intelligence System (controlled scaffold).

Voice → STT → Understanding → Reasoning → TTS
Uses local hooks when available; never pretends hardware is present.
"""
from __future__ import annotations

from typing import Any


class VoiceIntelligence:
    def understand_audio(self, audio_path: str) -> dict[str, Any]:
        """Speech-to-text when a backend is configured."""
        try:
            # Optional local STT hook
            from om_ai.perception.audio import transcribe  # type: ignore

            text = transcribe(audio_path)
            return {"ok": bool(text), "text": text or "", "path": audio_path}
        except Exception:
            return {
                "ok": False,
                "text": "",
                "path": audio_path,
                "reason": "STT backend not installed — set up whisper/local STT",
            }

    def speak(self, text: str) -> dict[str, Any]:
        """Text-to-speech when a backend is configured."""
        try:
            from om_ai.perception.audio import synthesize  # type: ignore

            path = synthesize(text)
            return {"ok": bool(path), "audio_path": path}
        except Exception:
            return {
                "ok": False,
                "text": text,
                "reason": "TTS backend not installed",
            }

    def conversation_turn(self, audio_path: str) -> dict[str, Any]:
        stt = self.understand_audio(audio_path)
        if not stt.get("ok"):
            return {"stage": "stt", **stt}
        reply = ""
        try:
            from om_ai.runtime.chat_pipeline import run_chat_pipeline

            out = run_chat_pipeline(str(stt.get("text") or ""))
            reply = str(out.get("answer") or "")
        except Exception as exc:
            reply = f"(voice brain error: {exc})"
        tts = self.speak(reply)
        return {
            "stage": "complete",
            "transcript": stt.get("text"),
            "reply": reply,
            "tts": tts,
        }
