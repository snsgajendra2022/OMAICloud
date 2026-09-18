"""STEP 40 — Voice runtime orchestration."""
from __future__ import annotations

import logging
import threading
from typing import Any, Callable

from .audio_device import AudioDeviceManager
from .audio_stream import AudioStream
from .echo_controller import EchoController
from .interruption_detector import InterruptionDetector
from .speech_recognizer import SpeechRecognizer
from .streaming_stt import StreamingSTT
from .streaming_tts import StreamingTTS
from .transcript_manager import TranscriptManager
from .voice_activity_detector import VoiceActivityDetector
from .voice_session import VoiceSession
from .voice_state import CompanionState, assert_transition
from .wake_word_engine import WakeWordEngine

logger = logging.getLogger(__name__)


class VoiceRuntime:
    def __init__(
        self,
        *,
        wake_phrase: str = "hey om",
        text_only: bool = False,
        wake_word_enabled: bool = True,
        on_event: Callable[[str, dict[str, Any]], None] | None = None,
        on_final_transcript: Callable[[str, VoiceSession], None] | None = None,
    ) -> None:
        self.text_only = text_only
        self.wake_word_enabled = wake_word_enabled and not text_only
        self.on_event = on_event
        self.on_final_transcript = on_final_transcript
        self.state = CompanionState.STARTING
        self.session = VoiceSession()
        self.devices = AudioDeviceManager()
        self.vad = VoiceActivityDetector()
        self.echo = EchoController()
        self.wake = WakeWordEngine(wake_phrase)
        self.recognizer = SpeechRecognizer()
        self.stt = StreamingSTT(self.recognizer)
        self.tts = StreamingTTS()
        self.transcripts = TranscriptManager()
        self.interrupt = InterruptionDetector(self.vad)
        self.stream = AudioStream(on_chunk=self._on_audio_chunk)
        self._lock = threading.RLock()
        self._ready = False

        self.tts.on_started = lambda: self._set_state(CompanionState.SPEAKING)
        self.tts.on_completed = lambda: self._after_speak()
        self.tts.on_cancelled = lambda: self._emit("tts.cancelled", {})

    def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        if self.on_event:
            try:
                self.on_event(event_type, payload)
            except Exception as exc:
                logger.debug("voice event handler error: %s", exc)

    def _set_state(self, new_state: CompanionState) -> None:
        with self._lock:
            try:
                assert_transition(self.state, new_state)
            except ValueError:
                # Allow recovery transitions
                pass
            self.state = new_state
        self._emit("companion.state", {"state": new_state.value})

    def start(self) -> dict[str, Any]:
        self._set_state(CompanionState.STARTING)
        audio_ok = True
        if not self.text_only:
            started = self.stream.start()
            audio_ok = bool(started.get("ok"))
        self._ready = True
        if self.wake_word_enabled:
            self.wake.arm()
            self._set_state(CompanionState.LISTENING_FOR_WAKE_WORD)
        else:
            self.session.activate()
            self._set_state(CompanionState.LISTENING if not self.text_only else CompanionState.READY)
        return {
            "ok": True,
            "text_only": self.text_only,
            "audio_ok": audio_ok or self.text_only,
            "state": self.state.value,
            "wake": self.wake.status(),
            "stt": self.recognizer.status(),
            "tts": self.tts.status(),
            "devices": self.devices.status(),
        }

    def stop(self) -> None:
        self._set_state(CompanionState.SHUTTING_DOWN)
        self.tts.cancel()
        self.stt.cancel()
        self.stream.stop()
        self.session.deactivate()
        self._ready = False

    def mute(self) -> None:
        self.session.muted = True
        self.tts.cancel()
        self._set_state(CompanionState.MUTED)
        self._emit("voice.muted", {})

    def unmute(self) -> None:
        self.session.muted = False
        if self.wake_word_enabled and not self.session.active:
            self._set_state(CompanionState.LISTENING_FOR_WAKE_WORD)
        else:
            self._set_state(CompanionState.LISTENING if not self.text_only else CompanionState.READY)

    def interrupt_speech(self) -> None:
        if self.tts.speaking:
            self.session.interrupted_assistant_text = self.session.last_assistant_text
            self.tts.cancel()
            self._set_state(CompanionState.INTERRUPTED)
            self._emit("voice.interrupted", {})
            self._set_state(CompanionState.LISTENING)

    def speak(self, text: str) -> dict[str, Any]:
        if self.session.muted or self.text_only:
            self.session.add_turn("assistant", text)
            return {"ok": True, "spoken": False, "text": text}
        self.echo.set_speaking(True)
        self.vad.energy_threshold = self.echo.effective_threshold()
        self.session.add_turn("assistant", text)
        return self.tts.speak(text)

    def _after_speak(self) -> None:
        self.echo.set_speaking(False)
        self.vad.energy_threshold = self.echo.effective_threshold()
        if self.session.active and not self.session.expired():
            self._set_state(CompanionState.LISTENING)
        elif self.wake_word_enabled:
            self.wake.arm()
            self._set_state(CompanionState.LISTENING_FOR_WAKE_WORD)
        else:
            self._set_state(CompanionState.IDLE)

    def ingest_text(self, text: str, *, from_wake: bool = False) -> dict[str, Any]:
        """Text-mode / final STT entry."""
        q = (text or "").strip()
        if not q:
            return {"ok": False, "reason": "empty"}
        if self.session.muted:
            return {"ok": False, "reason": "muted"}

        # Pending yes/no for permission
        if self.session.pending_permission_id and q.lower() in {"yes", "y", "ok", "okay", "allow", "confirm"}:
            return {
                "ok": True,
                "permission_response": "approve",
                "permission_id": self.session.pending_permission_id,
                "text": q,
                "session": self.session.to_dict(),
            }
        if self.session.pending_permission_id and q.lower() in {"no", "n", "deny", "cancel", "stop"}:
            return {
                "ok": True,
                "permission_response": "deny",
                "permission_id": self.session.pending_permission_id,
                "text": q,
                "session": self.session.to_dict(),
            }

        if self.wake_word_enabled and not self.session.active:
            wake = self.wake.detect_text(q)
            if wake.get("detected") or from_wake:
                self.session.activate()
                self.wake.disarm()
                self._set_state(CompanionState.ACTIVATING)
                self._emit("voice.wake", wake)
                # Strip wake phrase from command if present
                remainder = q
                for p in (self.wake.phrase, "hey om", "hi om"):
                    if remainder.lower().startswith(p):
                        remainder = remainder[len(p):].strip(" ,.-")
                        break
                self._set_state(CompanionState.LISTENING)
                if not remainder:
                    return {
                        "ok": True,
                        "wake_only": True,
                        "prompt": "Yes?",
                        "session": self.session.to_dict(),
                    }
                q = remainder
            else:
                return {"ok": False, "reason": "waiting_for_wake", "wake": wake}

        if self.session.expired():
            self.session.deactivate()
            if self.wake_word_enabled:
                self.wake.arm()
                self._set_state(CompanionState.LISTENING_FOR_WAKE_WORD)
                return {"ok": False, "reason": "session_expired"}

        self._set_state(CompanionState.TRANSCRIBING)
        turn = self.transcripts.commit_final(q)
        self.session.add_turn("user", q)
        self._emit("stt.final", turn.to_dict())
        self._set_state(CompanionState.UNDERSTANDING)
        if self.on_final_transcript:
            self.on_final_transcript(q, self.session)
        return {"ok": True, "text": q, "session": self.session.to_dict(), "turn": turn.to_dict()}

    def _on_audio_chunk(self, samples) -> None:
        if self.text_only or self.session.muted or not self._ready:
            return
        # Barge-in
        if self.tts.speaking:
            hit = self.interrupt.check(samples, assistant_speaking=True)
            if hit.get("interrupted"):
                self.interrupt_speech()
            return
        vad = self.vad.process(samples)
        if vad.speech_started:
            self._set_state(CompanionState.SPEECH_DETECTED)
            self._emit("voice.speech_started", self.vad.to_dict(vad))
        partial = self.stt.push(samples)
        if partial and partial.get("text"):
            self.transcripts.set_partial(str(partial["text"]), confidence=float(partial.get("confidence") or 0))
            self._emit("stt.partial", partial)
            if self.wake_word_enabled and not self.session.active:
                wake = self.wake.detect_text(str(partial["text"]))
                if wake.get("detected"):
                    self.session.activate()
                    self.wake.disarm()
                    self._emit("voice.wake", wake)
                    self._set_state(CompanionState.LISTENING)
        if vad.speech_ended:
            self._emit("voice.speech_ended", self.vad.to_dict(vad))
            final = self.stt.finalize()
            text = str(final.get("text") or "").strip()
            if text:
                self.ingest_text(text)

    def status(self) -> dict[str, Any]:
        return {
            "ready": self._ready,
            "state": self.state.value,
            "text_only": self.text_only,
            "session": self.session.to_dict(),
            "wake": self.wake.status(),
            "stt": self.stt.status(),
            "tts": self.tts.status(),
            "stream": self.stream.status(),
            "devices": self.devices.status(),
        }
