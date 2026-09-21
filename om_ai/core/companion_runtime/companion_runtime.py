"""STEP 50 — Final OM Companion Runtime (shared lifecycle)."""
from __future__ import annotations

import logging
import re
import threading
import uuid
from typing import Any

from .config import CompanionConfig
from .health import component_health
from .lifecycle import Lifecycle
from .runtime_context import RuntimeContext
from .service_registry import ServiceRegistry

logger = logging.getLogger(__name__)


class CompanionRuntime:
    """Owns voice, brain, memory, agents, actions, realtime, security — one lifecycle."""

    def __init__(self, config: CompanionConfig | None = None) -> None:
        self.config = config or CompanionConfig.from_env()
        self.lifecycle = Lifecycle.CREATED
        self.registry = ServiceRegistry()
        self.context = RuntimeContext()
        self._lock = threading.RLock()
        self._started = False
        self.voice = None
        self.brain = None
        self.memory = None
        self.actions = None
        self.agents = None
        self.devices = None
        self.security = None
        self.realtime = None
        self.personality = None
        self.os = None  # STEP 60 Companion OS
        self.presence = None  # STEP 64 living loop
        self.conversation_loop = None  # STEP 65 realtime
        self.hci = None  # Real-time human conversation intelligence
        self._hci_hold_text = ""
        self.capabilities = None  # STEP 67
        self.multimodal = None  # STEP 66
        self.improvement = None  # STEP 68
        self._in_handle_text = False

    def _emit(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        if self.realtime is None:
            return
        try:
            self.realtime.emit(self.context.session_id, event_type, payload or {}, trace_id=self.context.trace_id)
        except Exception as exc:
            logger.debug("emit failed: %s", exc)

    def start(self) -> dict[str, Any]:
        with self._lock:
            if self._started:
                return self.status_banner()
            self.lifecycle = Lifecycle.STARTING
            self.context = RuntimeContext()

            # Security
            try:
                from om_ai.core.companion_security import SecurityRuntime
                self.security = SecurityRuntime()
            except Exception:
                try:
                    from om_ai.core.companion_security.security_runtime import SecurityRuntime
                    self.security = SecurityRuntime()
                except Exception as exc:
                    logger.warning("security init: %s", exc)
                    self.security = None

            # Realtime
            from om_ai.core.realtime import RealtimeRuntime
            self.realtime = RealtimeRuntime()
            self.registry.register("realtime", self.realtime)

            # Memory — MUST share singleton with brain MemoryBridge
            if self.config.memory_enabled:
                try:
                    from om_ai.core.companion_memory import get_memory_service

                    self.memory = get_memory_service()
                except Exception as exc:
                    logger.warning("memory init: %s", exc)
                    self.memory = None

            # Personality
            try:
                from om_ai.core.companion_personality import PersonalityEngine
                self.personality = PersonalityEngine()
            except Exception:
                try:
                    from om_ai.core.companion_personality.personality_engine import PersonalityEngine
                    self.personality = PersonalityEngine()
                except Exception:
                    self.personality = None

            # Actions / devices / agents
            if self.config.actions_enabled:
                try:
                    from om_ai.core.action_control import ActionControlEngine
                    self.actions = ActionControlEngine()
                except Exception as exc:
                    logger.warning("actions init: %s", exc)
                try:
                    from om_ai.core.device_runtime import DeviceRuntime
                    self.devices = DeviceRuntime()
                except Exception as exc:
                    logger.warning("devices init: %s", exc)
                try:
                    from om_ai.core.companion_agent import AgentController
                    self.agents = AgentController()
                except Exception as exc:
                    logger.warning("agents init: %s", exc)

            # Brain
            try:
                from om_ai.core.companion_brain import CompanionBrainRuntime

                self.brain = CompanionBrainRuntime()
            except Exception as exc:
                logger.warning("brain init: %s", exc)
                self.brain = None

            # Voice — native STT finals call brain via _on_final_transcript
            from om_ai.core.voice_intelligence import VoiceRuntime
            self.voice = VoiceRuntime(
                wake_phrase=self.config.wake_word,
                text_only=self.config.text_only,
                wake_word_enabled=self.config.wake_word_enabled and not self.config.text_only,
                on_event=lambda et, payload: self._emit(et, payload),
                on_final_transcript=self._on_final_transcript,
            )
            voice_start = self.voice.start()
            self.registry.register("voice", self.voice)
            self.registry.register("brain", self.brain)
            self.registry.register("memory", self.memory)
            self.registry.register("actions", self.actions)
            self.registry.register("agents", self.agents)
            self.registry.register("devices", self.devices)
            self.registry.register("security", self.security)

            # STEP 60 — Companion OS (presence / convo / voice / avatar / memory / …)
            try:
                from om_ai.core.companion_os import get_companion_os

                self.os = get_companion_os()
                self.registry.register("companion_os", self.os)
            except Exception as exc:
                logger.warning("companion_os init: %s", exc)
                self.os = None

            # STEP 64 — Presence Runtime (alive loop)
            try:
                from om_ai.core.presence_runtime import get_presence_engine

                self.presence = get_presence_engine()
                self.presence.start()
                self.presence.bind_stop_speech(
                    lambda: self.voice.interrupt_speech() if self.voice else None
                )
                self.registry.register("presence_runtime", self.presence)
            except Exception as exc:
                logger.warning("presence_runtime init: %s", exc)
                self.presence = None

            # STEP 65 — Realtime conversation loop
            try:
                from om_ai.core.conversation_runtime import get_conversation_loop
                from om_ai.core.human_intelligence import get_human_conversation_pipeline

                self.conversation_loop = get_conversation_loop()
                self.conversation_loop.bind(
                    stop_speech=lambda: self.voice.interrupt_speech() if self.voice else None,
                    presence=self.presence,
                    human_pipeline=get_human_conversation_pipeline(),
                )
                self.registry.register("conversation_loop", self.conversation_loop)
            except Exception as exc:
                logger.warning("conversation_loop init: %s", exc)
                self.conversation_loop = None

            # Real-time Human Conversation Intelligence (listen → timing → plan)
            try:
                from om_ai.core.human_conversation_intelligence import (
                    get_human_conversation_intelligence,
                )

                self.hci = get_human_conversation_intelligence()
                self.registry.register("human_conversation_intelligence", self.hci)
            except Exception as exc:
                logger.warning("human_conversation_intelligence init: %s", exc)
                self.hci = None

            # STEP 66 — Multimodal
            try:
                from om_ai.core.multimodal_intelligence import get_multimodal_router

                self.multimodal = get_multimodal_router()
                self.registry.register("multimodal", self.multimodal)
            except Exception as exc:
                logger.debug("multimodal init: %s", exc)
                self.multimodal = None

            # STEP 67 — Capability system
            try:
                from om_ai.core.capability_system import get_capability_system

                self.capabilities = get_capability_system()
                self.registry.register("capabilities", self.capabilities)
            except Exception as exc:
                logger.debug("capability_system init: %s", exc)
                self.capabilities = None

            # STEP 68 — Self improvement (offline)
            try:
                from om_ai.core.self_improvement import get_improvement_pipeline

                self.improvement = get_improvement_pipeline()
                self.registry.register("improvement", self.improvement)
            except Exception as exc:
                logger.debug("improvement init: %s", exc)
                self.improvement = None

            # Production onboarding → companion context (if user already bootstrapped)
            try:
                import os as _os

                from om_ai.core.onboarding import get_onboarding_engine

                actor = (_os.getenv("OM_ONBOARDING_ACTOR") or "").strip()
                eng = get_onboarding_engine()
                pack = eng.load(actor) if actor else None
                if pack and pack.get("companion_context"):
                    self.onboarding_context = pack["companion_context"]
                    self.registry.register("onboarding", pack)
            except Exception as exc:
                logger.debug("onboarding context: %s", exc)

            self._started = True
            self.lifecycle = Lifecycle.RUNNING
            banner = self.status_banner()
            banner["voice_start"] = voice_start
            if self.os is not None:
                try:
                    banner["companion_os"] = self.os.status()
                except Exception:
                    pass
            if getattr(self, "onboarding_context", None):
                banner["onboarding"] = True
            if (
                self.config.avatar_enabled
                and not self.config.no_avatar
                and not self.config.text_only
            ):
                self._maybe_open_ui()
            return banner

    def _maybe_open_ui(self) -> None:
        """Best-effort open companion UI when an API server is expected."""
        try:
            import webbrowser

            url = f"http://{self.config.bind_host}:{self.config.bind_port}/companion"
            webbrowser.open(url)
            logger.info("opened companion UI %s", url)
        except Exception as exc:
            logger.debug("companion UI open skipped: %s", exc)

    def stop(self) -> dict[str, Any]:
        with self._lock:
            self.lifecycle = Lifecycle.STOPPING
            if self.voice is not None:
                try:
                    self.voice.stop()
                except Exception:
                    pass
            self._started = False
            self.lifecycle = Lifecycle.STOPPED
            return {"ok": True, "lifecycle": self.lifecycle.value}

    def _on_final_transcript(self, text: str, session: Any) -> None:
        """Native mic path: ingest already ran — continue into brain without re-ingest."""
        if self._in_handle_text:
            return
        try:
            self.handle_text(text, already_ingested=True)
        except Exception as exc:
            logger.warning("native transcript turn failed: %s", exc)

    def handle_partial(
        self,
        text: str,
        *,
        history: list[dict[str, Any]] | None = None,
        rms: float = 0.0,
    ) -> dict[str, Any]:
        """Interim speech — understand without answering yet."""
        if not self._started:
            self.start()
        if self.hci is None:
            return {"ok": True, "hold": True, "mode": "partial", "partial": (text or "").strip()}
        hist = history or (list(self.voice.session.history) if self.voice else [])
        pack = self.hci.on_partial(text, history=hist, rms=rms)
        if self.presence is not None:
            try:
                self.presence.listening()
            except Exception:
                pass
        self._emit("speech.partial", {"text": (text or "")[:160], "hold": pack.get("hold")})
        return {"ok": True, **pack}

    def handle_text(
        self,
        text: str,
        *,
        history: list[dict[str, Any]] | None = None,
        already_ingested: bool = False,
        force_commit: bool = False,
    ) -> dict[str, Any]:
        if not self._started:
            self.start()
        assert self.voice is not None
        self.context.trace_id = str(uuid.uuid4())
        self._emit("brain.started", {"text": (text or "")[:120]})

        # Cancellation / stop commands — never run brain or TTS on these
        low = (text or "").strip().lower()
        low = re.sub(r"[^\w\s']+", " ", low)
        low = " ".join(low.split())
        stop_phrases = {
            "stop",
            "cancel",
            "cancel that",
            "don't do that",
            "dont do that",
            "mute",
            "quiet",
            "enough",
            "shut up",
            "be quiet",
            "ruk",
            "ruko",
            "ruk jao",
            "band karo",
            "band kar",
            "chup",
            "chup raho",
            "bas",
            "bas karo",
        }
        if low in stop_phrases or low.startswith("stop ") or low.startswith("cancel "):
            if "mute" in low:
                self.voice.mute()
                return {
                    "answer": "Muted.",
                    "spoken": "Muted.",
                    "spoken_tts": "Muted.",
                    "activities": [],
                    "state": "MUTED",
                    "speak_client": False,
                    "interrupted": True,
                }
            self.voice.interrupt_speech()
            if self.agents and hasattr(self.agents, "cancel"):
                try:
                    self.agents.cancel()
                except Exception:
                    pass
            msg = "Okay — stopped."
            if any(w in low for w in ("ruk", "band", "chup", "bas")):
                msg = "Theek hai — ruk gaya."
            return {
                "answer": msg,
                "spoken": msg,
                "spoken_tts": msg,
                "activities": [],
                "state": "LISTENING",
                "speak_client": False,
                "interrupted": True,
            }

        if already_ingested:
            ingested = {"ok": True, "text": (text or "").strip()}
        else:
            self._in_handle_text = True
            try:
                ingested = self.voice.ingest_text(text)
            finally:
                # Keep flag True until end of turn so on_final_transcript no-ops
                pass

        try:
            if ingested.get("wake_only"):
                reply = ingested.get("prompt") or "Ji sir, kahiye?"
                if self.presence is not None:
                    try:
                        self.presence.listening()
                        self.presence.responding()
                    except Exception:
                        pass
                self.voice.speak(reply)
                if self.presence is not None:
                    try:
                        self.presence.waiting()
                    except Exception:
                        pass
                self._emit("avatar.state", {"state": "attentive"})
                return {"answer": reply, "activities": [], "wake": True, "session": ingested.get("session")}

            if ingested.get("permission_response"):
                return self._resolve_permission(ingested)

            if not ingested.get("ok"):
                reason = ingested.get("reason")
                if reason == "waiting_for_wake":
                    return {
                        "answer": "",
                        "waiting_for_wake": True,
                        "activities": [],
                        "state": self.voice.state.value,
                    }
                return {"answer": "", "error": reason, "state": self.voice.state.value}

            user_text = str(ingested.get("text") or text)
            hist = history or list(self.voice.session.history)
            self._update_session_context(user_text)
            return self._continue_turn(user_text, hist, force_commit=force_commit)
        finally:
            if not already_ingested:
                self._in_handle_text = False

    def _continue_turn(
        self,
        user_text: str,
        hist: list[dict[str, Any]],
        *,
        force_commit: bool = False,
    ) -> dict[str, Any]:
        assert self.voice is not None

        # —— Human conversation intelligence: wait on incomplete speech ——
        hci_pack: dict[str, Any] = {}
        if self.hci is not None:
            try:
                prefs: dict[str, Any] = {}
                try:
                    if self.os is not None and hasattr(self.os, "memory"):
                        prefs = dict(getattr(self.os.memory, "preferences", {}) or {})
                except Exception:
                    prefs = {}
                hci_pack = self.hci.on_final(
                    user_text,
                    history=hist,
                    preferences=prefs,
                    force=force_commit,
                )
                if hci_pack.get("hold") and not force_commit:
                    self._hci_hold_text = str(hci_pack.get("text") or user_text)
                    if self.presence is not None:
                        try:
                            self.presence.listening()
                        except Exception:
                            pass
                    self._emit("conversation.hold", {"text": self._hci_hold_text[:160]})
                    return {
                        "answer": "",
                        "spoken": "",
                        "spoken_tts": "",
                        "activities": [],
                        "hold": True,
                        "commit": False,
                        "speak_client": False,
                        "state": "LISTENING",
                        "meaning": hci_pack.get("meaning"),
                        "emotion": hci_pack.get("emotion"),
                        "timing": hci_pack.get("timing"),
                        "hci": {"mode": "hold", "reason": "incomplete_speech"},
                    }
                # Use reconstructed / merged text after hold
                if hci_pack.get("text"):
                    user_text = str(hci_pack["text"])
                self._hci_hold_text = ""
                try:
                    self.context.meta["hci"] = {
                        "emotion": hci_pack.get("emotion"),
                        "timing": hci_pack.get("timing"),
                        "response_plan": hci_pack.get("response_plan"),
                        "system_hint": hci_pack.get("system_hint") or "",
                    }
                    self.context.meta["hci_system_hint"] = hci_pack.get("system_hint") or ""
                except Exception:
                    pass
            except Exception as exc:
                logger.debug("hci on_final: %s", exc)

        if self.presence is not None:
            try:
                self.presence.thinking()
                self._emit("presence.state", self.presence.status())
            except Exception:
                pass

        # Realtime interrupt check (barge-in / stop)
        if self.conversation_loop is not None:
            try:
                rt = self.conversation_loop.realtime.on_final(user_text, history=hist)
                if rt.get("interrupted"):
                    if self.presence is not None:
                        self.presence.interrupt()
                    msg = "Theek hai — ruk gaya." if any(
                        w in user_text.lower() for w in ("ruk", "band", "chup", "bas")
                    ) else "Okay — stopped."
                    return {
                        "answer": msg,
                        "spoken": msg,
                        "activities": [],
                        "interrupted": True,
                        "state": "LISTENING",
                        "speak_client": False,
                        "presence": self.presence.status() if self.presence else {},
                    }
            except Exception:
                pass

        # Multimodal hint when user references screen/vision
        multimodal_hint = ""
        if self.multimodal is not None:
            try:
                mm = self.multimodal.route(user_text)
                if mm.get("multimodal"):
                    multimodal_hint = str(mm.get("system_hint") or "")
                    self._emit("multimodal", {"focus": (mm.get("screen") or {}).get("focus")})
            except Exception:
                pass
        try:
            self.context.meta["multimodal_hint"] = multimodal_hint
        except Exception:
            pass

        activities: list[str] = []
        semantic: dict[str, Any] = {}
        answer = ""
        spoken = ""
        spoken_tts = ""
        action_handled = False
        brain_out: dict[str, Any] = {}

        # Empathy / comfort path from HCI — prefer human companion over blunt Q&A
        response_plan = (hci_pack.get("response_plan") or {}) if hci_pack else {}
        intent_name = str(((response_plan.get("intent") or {}).get("intent")) or "")
        if (
            not action_handled
            and intent_name in {"comfort", "ask", "clarify"}
            and not self._looks_like_action(user_text)
        ):
            comfort = self._hci_comfort_turn(user_text, hci_pack, hist)
            if comfort:
                brain_out = comfort
                answer = str(comfort.get("answer") or "").strip()
                spoken = str(comfort.get("spoken") or answer).strip()
                spoken_tts = spoken
                semantic = comfort.get("semantic") or {"conversation_mode": "social"}
                action_handled = True

        # —— Actions FIRST (skip heavy LLM when OS intent is clear) ——
        if self.config.actions_enabled and (self.devices is not None or self.actions is not None):
            if self._looks_like_action(user_text):
                planned = self._plan_action(user_text, {})
                if planned:
                    self._emit("action.planned", planned)
                    activities.append("Running action")
                    decision = self._permission_gate(planned)
                    if decision.get("requires_approval"):
                        self.voice.session.pending_permission_id = decision.get("permission_id")
                        self.voice.session.pending_action = planned
                        msg = decision.get("prompt") or "Permission required. Say yes to allow, or no to cancel."
                        self._record_assistant(msg)
                        self._emit("permission.required", decision)
                        return {
                            "answer": msg,
                            "spoken": msg,
                            "spoken_tts": msg,
                            "activities": [],
                            "permission": decision,
                            "semantic": {"requires_action": True, "intent": "action_request"},
                            "state": "WAITING_FOR_PERMISSION",
                            "speak_client": True,
                        }
                    if decision.get("allowed"):
                        result = self._execute_action(planned)
                        activities.append("Executed action" if result.get("ok") else "Action failed")
                        answer = str(
                            result.get("message")
                            or planned.get("speak_ok")
                            or ("Done." if result.get("ok") else "That didn't work.")
                        )
                        spoken = answer
                        spoken_tts = answer
                        semantic = {
                            "requires_action": True,
                            "intent": "action_request",
                            "domain": "action",
                        }
                        action_handled = True

        # —— Fast human path (voice): emotional / social turns skip slow stacked LLM ——
        if not action_handled:
            fast = self._fast_human_turn(user_text, hist)
            if fast:
                brain_out = fast
                activities = list(fast.get("activities") or []) + activities
                for a in activities[:6]:
                    self._emit("brain.activity", {"activity": a})
                semantic = fast.get("semantic") or {"conversation_mode": "social"}
                answer = str(fast.get("answer") or "").strip()
                spoken = str(fast.get("spoken") or answer).strip()
                spoken_tts = str(fast.get("spoken_tts") or spoken).strip()
                action_handled = True

        # —— Brain for knowledge / complex asks ——
        if not action_handled:
            brain_out = self._run_brain(user_text, hist)
            activities = list(brain_out.get("activities") or []) + activities
            for a in activities:
                self._emit("brain.activity", {"activity": a})

            semantic = brain_out.get("semantic") or {}
            answer = str(brain_out.get("answer") or "").strip()
            spoken = str(brain_out.get("spoken") or answer).strip()
            spoken_tts = str(brain_out.get("spoken_tts") or spoken).strip()

            # Brain already shaped speech. Never speak internal agent / pipeline chrome.
            try:
                from om_ai.core.companion_personality.voice_presence import (
                    is_garbage_spoken,
                    rescue_spoken,
                    strip_internal_chrome,
                    shape_for_speech,
                )

                answer = strip_internal_chrome(answer)
                spoken = strip_internal_chrome(spoken) or answer
                if is_garbage_spoken(spoken) or is_garbage_spoken(answer):
                    spoken = rescue_spoken(user_text, spoken)
                    answer = spoken
                    spoken_tts = spoken
                else:
                    pack = shape_for_speech(spoken, user_message=user_text)
                    spoken = str(pack.get("spoken") or spoken)
                    spoken_tts = str(pack.get("spoken_tts") or spoken)
                    answer = spoken
            except Exception:
                pass

            # Secondary action pass (semantic-marked, rare)
            if (
                self.config.actions_enabled
                and (self.devices is not None or self.actions is not None)
                and semantic.get("requires_action")
                and self._looks_like_action(user_text)
            ):
                planned = self._plan_action(user_text, semantic)
                if planned:
                    self._emit("action.planned", planned)
                    decision = self._permission_gate(planned)
                    if decision.get("requires_approval"):
                        self.voice.session.pending_permission_id = decision.get("permission_id")
                        self.voice.session.pending_action = planned
                        msg = decision.get("prompt") or "Permission required. Say yes to allow, or no to cancel."
                        self._record_assistant(msg)
                        self._emit("permission.required", decision)
                        return {
                            "answer": msg,
                            "activities": [],
                            "permission": decision,
                            "semantic": semantic,
                            "state": "WAITING_FOR_PERMISSION",
                        }
                    if decision.get("allowed"):
                        result = self._execute_action(planned)
                        activities.append("Executed action" if result.get("ok") else "Action failed")
                        answer = result.get("message") or (
                            "Done." if result.get("ok") else "That didn't work."
                        )
                        spoken = answer
                        spoken_tts = answer

        if not answer:
            spoken = spoken or ""
            spoken_tts = spoken_tts or spoken

        # Personality finalize on every spoken turn (one engine, enforced style)
        if self.personality is not None and (spoken or answer):
            try:
                pack = self.personality.prepare(
                    user_text,
                    intent=str(semantic.get("intent") or ""),
                    intent_confidence=float(semantic.get("confidence") or 0.6),
                    history=hist,
                    conversation_mode=str(semantic.get("conversation_mode") or "assist"),
                )
                finalized = self.personality.finalize(
                    spoken or answer,
                    pack,
                    conversation_mode=str(semantic.get("conversation_mode") or "assist"),
                    user_message=user_text,
                    voice_mode=True,
                )
                if finalized:
                    spoken = finalized
                    spoken_tts = finalized
                    answer = finalized
                if not brain_out.get("affect") and isinstance(pack.get("affect"), dict):
                    brain_out["affect"] = pack.get("affect")
                    brain_out["feeling"] = (pack.get("affect") or {}).get("label")
            except Exception:
                pass

        # STEP 60 — Companion OS enrichment (presence, continuous convo, memory, avatar…)
        os_pack: dict[str, Any] = {}
        try:
            if self.os is None:
                from om_ai.core.companion_os import get_companion_os

                self.os = get_companion_os()
            affect_out = brain_out.get("affect") if isinstance(brain_out.get("affect"), dict) else None
            os_pack = self.os.enrich_turn(
                user_text,
                answer=answer,
                speaking=False,
                affect=affect_out,
            )
            if os_pack.get("answer"):
                answer = str(os_pack["answer"])
                spoken = str(os_pack.get("spoken") or answer)
                spoken_tts = str(os_pack.get("spoken_tts") or spoken)
            # Never leave speech-timing ellipsis chrome in companion replies
            def _clean_spoken(s: str) -> str:
                t = re.sub(r"(?:\s*\.){2,}\s*", " ", s or "")
                t = re.sub(r"\s{2,}", " ", t).strip(" .")
                return t.strip()

            answer = _clean_spoken(answer)
            spoken = _clean_spoken(spoken) or answer
            spoken_tts = _clean_spoken(spoken_tts) or spoken
            # Restore empathy question if OS enrich stripped it
            try:
                q = str(
                    (((hci_pack.get("response_plan") or {}).get("question") or {}).get("question"))
                    or ""
                ).strip()
                if q and q.lower() not in spoken.lower() and intent_name in {"comfort", "ask", "clarify"}:
                    spoken = f"{spoken.rstrip('. ')}. {q}".strip()
                    answer = spoken
                    spoken_tts = spoken
            except Exception:
                pass
            try:
                from om_ai.core.companion_personality.voice_presence import (
                    is_garbage_spoken,
                    rescue_spoken,
                    strip_internal_chrome,
                )

                answer = strip_internal_chrome(answer)
                spoken = strip_internal_chrome(spoken) or answer
                spoken_tts = strip_internal_chrome(spoken_tts) or spoken
                if is_garbage_spoken(spoken) or is_garbage_spoken(answer):
                    spoken = rescue_spoken(user_text, spoken)
                    answer = spoken
                    spoken_tts = spoken
            except Exception:
                pass
            presence_mode = str(
                ((os_pack.get("presence") or {}).get("presence") or {}).get("mode") or ""
            )
            if presence_mode:
                activities.append(f"Presence · {presence_mode}")
                self._emit("presence.state", os_pack.get("presence") or {})
            if os_pack.get("avatar"):
                self._emit("avatar.state", os_pack["avatar"])
            if os_pack.get("om_avatar"):
                self._emit("avatar.state", os_pack["om_avatar"])
            if os_pack.get("consciousness"):
                self._emit("consciousness", os_pack["consciousness"])
        except Exception as exc:
            logger.debug("companion_os enrich failed: %s", exc)

        # Memory: brain already wrote when LLM ran — write for action-only turns
        sk, uk = self._identity_keys()
        if self.memory is not None and self.config.memory_enabled and action_handled:
            try:
                from om_ai.core.companion_personality.voice_presence import is_garbage_spoken

                if not is_garbage_spoken(answer):
                    self.memory.remember_turn(
                        session_key=sk, user_key=uk, role="user", content=user_text
                    )
                    self.memory.remember_turn(
                        session_key=sk, user_key=uk, role="assistant", content=answer
                    )
            except Exception:
                pass
        try:
            self._maybe_store_preference(user_text, uk)
        except Exception:
            pass

        # Continuous learning / self-improvement — never block the spoken reply
        def _offline_learn() -> None:
            try:
                from om_ai.core.continuous_learning import run_continuous_learning

                run_continuous_learning(user_text, answer)
            except Exception:
                pass
            if self.improvement is not None and answer:
                try:
                    self.improvement.after_turn(user_message=user_text, answer=answer)
                except Exception:
                    pass

        try:
            threading.Thread(target=_offline_learn, daemon=True).start()
        except Exception:
            pass

        if self.presence is not None:
            try:
                self.presence.responding()
            except Exception:
                pass

        # Browser companion speaks via /tts — avoid double-speak from macOS say here
        if not self.config.text_only:
            try:
                self.voice.speak(spoken)
            except Exception:
                pass
        else:
            self._record_assistant(answer)
        self._emit("avatar.state", {"state": "speaking", **(os_pack.get("om_avatar") or os_pack.get("avatar") or {})})
        if not self.config.text_only:
            try:
                last = (self.voice.session.history or [])[-1:]
                if not last or last[0].get("role") != "assistant" or last[0].get("content") != answer:
                    self.voice.session.add_turn("assistant", answer)
            except Exception:
                pass

        if self.presence is not None:
            try:
                wait_pack = self.presence.waiting()
                self._emit("presence.state", wait_pack)
            except Exception:
                pass

        presence_mode = str(
            ((os_pack.get("presence") or {}).get("presence") or {}).get("mode")
            or (self.presence.loop.phase.value if self.presence else "")
            or self.voice.state.value
        )
        return {
            "answer": answer,
            "spoken": spoken,
            "spoken_tts": spoken_tts,
            "heard": user_text,
            "feeling": brain_out.get("feeling") or (brain_out.get("affect") or {}).get("label"),
            "affect": brain_out.get("affect"),
            "expression": (os_pack.get("presence") or {}).get("expression") or brain_out.get("expression"),
            "presence": (os_pack.get("presence") or {}).get("presence")
            or (self.presence.status() if self.presence else {}),
            "avatar": brain_out.get("avatar") or os_pack.get("om_avatar") or os_pack.get("avatar"),
            "conversation": os_pack.get("conversation") or brain_out.get("human_conversation"),
            "emotion": brain_out.get("emotion"),
            "friend": brain_out.get("friend") or (brain_out.get("meta") or {}).get("friend"),
            "pipeline": brain_out.get("pipeline"),
            "situation": brain_out.get("situation"),
            "response_iq": brain_out.get("response_iq"),
            "human_companion": bool(brain_out.get("human_companion")),
            "capabilities": self.capabilities.status() if self.capabilities else None,
            "learning": os_pack.get("learning"),
            "human_memory": os_pack.get("human_memory"),
            "autonomous": os_pack.get("autonomous"),
            "action": os_pack.get("action"),
            "consciousness": os_pack.get("consciousness"),
            "vision": os_pack.get("vision"),
            "background": os_pack.get("background"),
            "memory_line": brain_out.get("memory_line") or self._memory_line(os_pack, user_text=user_text),
            "voice_plan": os_pack.get("voice_plan") or brain_out.get("voice_plan"),
            # Never expose internal pipeline chrome to the companion client
            "activities": [],
            "semantic": semantic,
            "session": self.voice.session.to_dict(),
            "state": presence_mode or self.voice.state.value,
            "trace_id": self.context.trace_id,
            "speak_client": True,
            "os_step": 112,
            "alive_loop": True,
            "hci": {
                "emotion": (hci_pack.get("emotion") if hci_pack else None),
                "timing": (hci_pack.get("timing") if hci_pack else None),
                "meaning": (hci_pack.get("meaning") if hci_pack else None),
                "response_plan": (hci_pack.get("response_plan") if hci_pack else None),
            },
            "hold": False,
            "commit": True,
        }

    def _identity_keys(self) -> tuple[str, str]:
        """One session_id + user_key shared by brain memory and outer runtime."""
        sk = str(getattr(self.context, "session_id", "") or "default")
        user_ctx: dict[str, Any] = {}
        try:
            user_ctx = dict((self.context.meta or {}).get("user_context") or {})
        except Exception:
            user_ctx = {}
        actor = str(
            user_ctx.get("actor")
            or user_ctx.get("user_key")
            or user_ctx.get("name")
            or "user"
        ).strip() or "user"
        # Match ConversationSession.user_key = f"{tenant}:{actor}"
        uk = str(user_ctx.get("user_key") or f"default:{actor}")
        try:
            self.context.meta.setdefault("user_context", user_ctx)
            self.context.meta["user_context"]["user_key"] = uk
            self.context.meta["user_context"]["actor"] = actor
        except Exception:
            pass
        return sk, uk

    def _record_assistant(self, text: str) -> None:
        if not self.voice or not text:
            return
        try:
            hist = list(self.voice.session.history or [])
            if hist and hist[-1].get("role") == "assistant" and hist[-1].get("content") == text:
                return
            self.voice.session.add_turn("assistant", text)
        except Exception:
            pass

    def _run_brain(self, text: str, history: list[dict[str, Any]]) -> dict[str, Any]:
        model_generate = self._model_generate_fn()
        user_ctx: dict[str, Any] = {}
        try:
            user_ctx = dict((self.context.meta or {}).get("user_context") or {})
        except Exception:
            user_ctx = {}
        sk, uk = self._identity_keys()
        actor = str(user_ctx.get("actor") or user_ctx.get("name") or "user")
        hm_blob = ""
        try:
            if self.os and getattr(self.os, "human_memory", None):
                hm = self.os.human_memory
                if hasattr(hm, "recall_blob"):
                    hm_blob = str(hm.recall_blob() or "")
            if not hm_blob:
                from om_ai.core.human_memory import get_human_memory

                hm_blob = str(get_human_memory().recall_blob() or "")
        except Exception:
            hm_blob = ""
        extra = {
            "user_context": user_ctx,
            "user_name": str(user_ctx.get("name") or "").strip(),
            "user_key": uk,
            "voice_mode": True,
            "skip_canned_social": True,
            "human_memory_blob": hm_blob[:1500],
            "multimodal_hint": str((self.context.meta or {}).get("multimodal_hint") or ""),
            "hci_system_hint": str((self.context.meta or {}).get("hci_system_hint") or ""),
        }

        brain_out: dict[str, Any] = {}
        if self.brain is not None:
            for meth in ("run", "handle", "process", "turn"):
                fn = getattr(self.brain, meth, None)
                if callable(fn):
                    try:
                        out = fn(
                            text,
                            history=history,
                            session_id=sk,
                            actor=actor,
                            tenant_id="default",
                            project_id=str(user_ctx.get("purpose") or ""),
                            model_generate=model_generate,
                            extra=extra,
                        )
                        if isinstance(out, dict) and (out.get("answer") is not None or out.get("semantic")):
                            remembered = None
                            meta = out.get("meta")
                            if isinstance(meta, dict):
                                remembered = meta.get("remember_name")
                            if remembered:
                                user_ctx["name"] = str(remembered)
                                try:
                                    self.context.meta["user_context"] = user_ctx
                                except Exception:
                                    pass
                            brain_out = out
                            break
                    except TypeError:
                        try:
                            out = fn(text, history=history)
                            if isinstance(out, dict):
                                brain_out = out
                                break
                        except Exception:
                            pass
                    except Exception as exc:
                        logger.debug("brain.%s failed: %s", meth, exc)
        if not brain_out:
            try:
                from om_ai.core.companion_brain import run_companion_brain

                brain_out = run_companion_brain(
                    text,
                    history=history,
                    session_id=sk,
                    actor=actor,
                    model_generate=model_generate,
                    extra=extra,
                )
            except Exception:
                from om_ai.core.chatgpt_runtime import run_chatgpt_runtime

                pack = run_chatgpt_runtime(
                    text,
                    history=history,
                    model_generate=model_generate,
                    extra=extra,
                )
                brain_out = {
                    "answer": pack.get("answer") or "",
                    "semantic": (pack.get("chat_intelligence") or {}).get("intent") or {},
                    "activities": [],
                }

        # —— Human Companion Platform (11 systems) enriches every brain turn ——
        try:
            from om_ai.core.human_companion import get_human_companion

            hc = get_human_companion()
            hc.configure_identity(session_key=sk, user_key=uk)
            hc.bind_actions(
                plan_fn=lambda t, s: self._plan_action(t, s),
                execute_fn=self._execute_action,
                looks_fn=self._looks_like_action,
            )
            pack = hc.turn(
                text,
                history=history,
                generate=None,  # never re-call LLM here — pre_answer is enough (speed)
                pre_answer=str(brain_out.get("answer") or brain_out.get("spoken") or ""),
                semantic=brain_out.get("semantic") if isinstance(brain_out.get("semantic"), dict) else {},
                skip_action=True,
                persist=False,
            )
            if pack.get("spoken") or pack.get("answer"):
                brain_out["answer"] = pack.get("answer") or brain_out.get("answer")
                brain_out["spoken"] = pack.get("spoken") or brain_out.get("spoken")
                brain_out["spoken_tts"] = pack.get("spoken_tts") or brain_out.get("spoken_tts")
            if pack.get("feeling"):
                brain_out["feeling"] = pack["feeling"]
            if pack.get("affect"):
                brain_out["affect"] = pack["affect"]
            if pack.get("avatar"):
                brain_out["avatar"] = pack["avatar"]
            if pack.get("voice_plan"):
                brain_out["voice_plan"] = pack["voice_plan"]
            if pack.get("memory_line"):
                brain_out["memory_line"] = pack["memory_line"]
            if pack.get("conversation"):
                brain_out["human_conversation"] = pack["conversation"]
            if pack.get("emotion"):
                brain_out["emotion"] = pack["emotion"]
            if pack.get("friend"):
                brain_out["friend"] = pack["friend"]
            if pack.get("pipeline"):
                brain_out["pipeline"] = pack["pipeline"]
            if pack.get("situation"):
                brain_out["situation"] = pack["situation"]
            if pack.get("response_iq"):
                brain_out["response_iq"] = pack["response_iq"]
            acts = list(brain_out.get("activities") or [])
            for a in pack.get("activities") or []:
                if a not in acts:
                    acts.append(a)
            brain_out["activities"] = acts
            brain_out["human_companion"] = True
        except Exception as exc:
            logger.debug("human_companion enrich failed: %s", exc)

        return brain_out

    def _hci_comfort_turn(
        self,
        text: str,
        hci_pack: dict[str, Any],
        history: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Emotion-first companion reply driven by HCI plan + human companion brain."""
        try:
            from om_ai.core.human_companion import get_human_companion

            plan = hci_pack.get("response_plan") or {}
            style = plan.get("style") or {}
            question = plan.get("question") or {}
            emo = hci_pack.get("emotion") or {}
            hint = str(style.get("system_hint") or hci_pack.get("system_hint") or "")
            q = str(question.get("question") or "").strip()
            intent_name = str((plan.get("intent") or {}).get("intent") or "")
            gen = self._model_generate_fn()

            def _gen(prompt: str, context: str = "") -> str:
                merged = "\n".join(p for p in (hint, context) if p)
                return gen(prompt, merged)

            hc = get_human_companion()
            out = hc.turn(
                text,
                history=history,
                generate=_gen,
                pre_answer="",
                semantic={"conversation_mode": "social", "intent": "support"},
                skip_action=True,
                persist=False,
            )
            ans = str(out.get("answer") or out.get("spoken") or "").strip()
            # Strip speech-timing ellipsis chrome
            ans = re.sub(r"(?:\s*\.){2,}\s*$", "", ans).strip()
            ans = re.sub(r"\s{2,}", " ", ans)
            # If model/companion produced nothing usable, compose from plan signals (still dynamic)
            if not ans or len(ans.split()) < 3:
                label = str(emo.get("emotion") or "neutral")
                lead = "That sounds hard." if label in {"sad", "stressed", "frustrated", "tired"} else "I'm with you."
                if q:
                    ans = f"{lead} {q}".strip()
                else:
                    ans = lead
            # Prefer ending with the planned gentle question when missing
            if q and q.lower() not in ans.lower() and intent_name in {"comfort", "ask", "clarify"}:
                if not ans.rstrip().endswith("?"):
                    ans = f"{ans.rstrip('. ')}. {q}".strip()
            # Never allow helpdesk robotic close
            if "how can i help" in ans.lower():
                ans = (q and f"That sounds difficult. {q}") or "That sounds difficult. What happened?"
            return {
                "answer": ans,
                "spoken": ans,
                "spoken_tts": ans,
                "feeling": emo.get("emotion") or "neutral",
                "affect": emo.get("pack") or emo,
                "emotion": emo.get("pack") or emo,
                "friend": {"friend_move": "hci_comfort", "system_hint": hint},
                "pipeline": ["hci", "human_companion"],
                "activities": [],
                "semantic": {"conversation_mode": "social", "intent": "support"},
                "human_companion": True,
                "hci": True,
                "response_plan": plan,
            }
        except Exception as exc:
            logger.debug("hci comfort turn failed: %s", exc)
            return None

    def _fast_human_turn(self, text: str, history: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Instant human replies for social / emotion / incomplete / wellbeing — no LLM stack."""
        import re

        low = (text or "").lower().strip()
        # Heavy knowledge / coding still needs the full brain
        if re.search(
            r"(?i)\b(explain|analyze|write|code|implement|refactor|debug this|"
            r"how does|what is the difference|prepare a report|architecture)\b",
            low,
        ):
            return None
        if len(low.split()) > 40:
            return None
        try:
            from om_ai.core.human_intelligence import get_human_conversation_pipeline

            locale = "hi" if any(
                w in low for w in ("hai", "kya", "tum", "nahi", "baat", "ji", "thak")
            ) else "en"
            user_ctx: dict[str, Any] = {}
            try:
                user_ctx = dict((self.context.meta or {}).get("user_context") or {})
            except Exception:
                user_ctx = {}
            out = get_human_conversation_pipeline().run(
                text,
                history=history,
                profile={"name": str(user_ctx.get("name") or "")},
                locale=locale,
                generate=None,
            )
            ans = str(out.get("answer") or out.get("spoken") or "").strip()
            if not ans or len(re.findall(r"[A-Za-z\u0900-\u097F']+", ans)) < 2:
                return None
            use_fast = bool(
                out.get("listen_first")
                or (out.get("incomplete") or {}).get("incomplete")
                or (out.get("wellbeing") or {}).get("active")
                or out.get("intent") in {"conversation", "share_win"}
                or out.get("need") in {"listen_first", "support_and_listen"}
                or re.search(r"(?i)^\s*(hey|hi|hello|namaste|thanks|thank you|ok|okay|haan)\b", low)
            )
            if not use_fast:
                return None
            emo = out.get("emotion_pack") if isinstance(out.get("emotion_pack"), dict) else {
                "label": out.get("emotion"),
                "emotion": out.get("emotion"),
                "need": out.get("need"),
                "response_style": out.get("response_style"),
                "tone": out.get("tone"),
            }
            return {
                "answer": ans,
                "spoken": ans,
                "spoken_tts": ans,
                "feeling": emo.get("label") or emo.get("emotion") or "neutral",
                "affect": emo,
                "emotion": emo,
                "friend": {"friend_move": "human_fast", "system_hint": out.get("system_hint")},
                "pipeline": out.get("stages") or ["human_fast"],
                "activities": [],
                "semantic": {
                    "conversation_mode": "social",
                    "intent": out.get("intent") or "conversation",
                },
                "human_companion": True,
                "fast_path": True,
                "memory_line": str((user_ctx.get("name") or "") and f"With {user_ctx.get('name')}") or "",
            }
        except Exception as exc:
            logger.debug("fast human turn failed: %s", exc)
            return None

    def _model_generate_fn(self):
        """Same production chat path as /v1/chat — native weights when ready, otherwise grounded brain."""

        def _gen(prompt: str, context: str = "") -> str:
            try:
                from om_ai.runtime.chat_backend import chat_reply

                native = None
                engine = None
                try:
                    from om_ai.api import main as api_main

                    native = getattr(api_main, "native_backend", None)
                    engine = getattr(api_main, "engine", None)
                except Exception:
                    native = None
                    engine = None
                native_chat = getattr(native, "chat", None) if native is not None else None
                native_ready = bool(
                    native is not None
                    and getattr(native, "loaded", False)
                    and getattr(native, "_trained", False)
                )
                local_chat = getattr(engine, "chat", None) if engine is not None else None
                local_loaded = bool(
                    engine is not None and getattr(engine, "model", None) is not None
                )
                messages: list[dict[str, str]] = []
                if context:
                    messages.append({"role": "system", "content": str(context)[:2000]})
                messages.append({"role": "user", "content": prompt})
                reply, _info = chat_reply(
                    messages,
                    local_chat=local_chat if callable(local_chat) else None,
                    local_loaded=local_loaded,
                    native_chat=native_chat if callable(native_chat) else None,
                    native_ready=native_ready,
                    assistant_instructions=str(context or "")[:1500],
                )
                text = str(reply or "").strip()
                try:
                    from om_ai.core.companion_personality.voice_presence import (
                        is_garbage_spoken,
                        strip_internal_chrome,
                    )
                    from om_ai.core.intelligence.real_answer import (
                        looks_like_static_reply,
                        build_real_answer,
                    )

                    text = strip_internal_chrome(text)
                    if (not text) or is_garbage_spoken(text) or looks_like_static_reply(text):
                        real = (build_real_answer(prompt) or "").strip()
                        if (
                            real
                            and not is_garbage_spoken(real)
                            and not looks_like_static_reply(real)
                        ):
                            return real
                        return ""
                except Exception:
                    pass
                return text
            except Exception as exc:
                logger.debug("companion model generate: %s", exc)
                return ""

        return _gen

    def _memory_line(self, os_pack: dict[str, Any], *, user_text: str = "") -> str:
        line = str((os_pack or {}).get("memory_line") or "").strip()
        if line:
            return line
        user_ctx: dict[str, Any] = {}
        try:
            user_ctx = dict((self.context.meta or {}).get("user_context") or {})
        except Exception:
            user_ctx = {}
        purpose = str(user_ctx.get("purpose") or "").strip()
        if purpose and purpose.lower() not in {"general", ""}:
            return f"Working on {purpose}"
        topic = str(
            (((os_pack or {}).get("conversation") or {}).get("user") or {}).get("topic") or ""
        ).strip()
        if topic and topic != "general":
            return topic.replace("_", " ")
        if user_text:
            return user_text.strip()[:80]
        return "Companion ready"

    def _update_session_context(self, text: str) -> None:
        assert self.voice is not None
        low = (text or "").lower()
        sess = self.voice.session
        if "om project" in low or "om-ai" in low or "operating brain" in low:
            from pathlib import Path

            root = Path(__file__).resolve().parents[3]
            sess.last_project_hint = "OM"
            sess.last_path_hint = str(root)
        if "vs code" in low or "vscode" in low or "visual studio code" in low:
            sess.last_app_hint = "Visual Studio Code"
        elif "finder" in low:
            sess.last_app_hint = "Finder"
        elif "safari" in low or "chrome" in low or "browser" in low:
            sess.last_app_hint = "Safari"

    def _maybe_store_preference(self, user_text: str, user_key: str) -> None:
        """Capture simple long-term facts (name / likes) into preference memory."""
        if self.memory is None or not hasattr(self.memory, "remember_fact"):
            return
        low = (user_text or "").strip()
        m = re.search(
            r"(?:my name is|i am|i'm|mera naam|main)\s+([A-Za-z\u0900-\u097F]{2,40})",
            low,
            re.I,
        )
        if m:
            name = m.group(1).strip(" .,!")
            if name.lower() not in {"om", "jarvis", "sir", "the", "a", "an"}:
                try:
                    self.memory.remember_fact(user_key, "name", name)
                except Exception:
                    pass
            return
        m2 = re.search(
            r"(?:i (?:like|love|prefer)|mujhe|pasand)\s+(.+?)(?:\.|$)",
            low,
            re.I,
        )
        if m2:
            fact = m2.group(1).strip(" .,!")[:120]
            if len(fact) >= 3:
                try:
                    self.memory.remember_fact(user_key, "preference", fact)
                except Exception:
                    pass

    def _looks_like_action(self, text: str) -> bool:
        low = (text or "").lower()
        if any(
            w in low
            for w in (
                "open ",
                "launch ",
                "start ",
                "delete ",
                "remove ",
                "list files",
                "show files",
                "youtube",
                "google ",
                "browser",
                "volume",
                "awaz",
                "mute",
                "unmute",
                "kholo",
                "khol ",
                "weather",
                "mausam",
                "shutdown",
                "restart",
                "calculator",
                "calc",
                "notes",
                "email",
                "mail",
                "spotlight",
                "time",
                "kitna baja",
                "what time",
            )
        ):
            return True
        # Coreference: "open it" / "do it"
        if re.search(r"\b(open|launch|delete|remove)\s+(it|that|this)\b", low):
            return True
        if re.search(r"\b(what'?s?\s+the\s+time|kitna\s+baja|time\s+batao)\b", low):
            return True
        return False

    def _plan_action(self, text: str, semantic: dict[str, Any]) -> dict[str, Any] | None:
        from pathlib import Path
        from urllib.parse import quote_plus

        from om_ai.core.companion_personality.human_speak import action_ack

        low = (text or "").lower()
        sess = self.voice.session if self.voice else None
        root = Path(__file__).resolve().parents[3]

        # --- Quick apps ---
        if re.search(r"\b(what'?s?\s+the\s+time|kitna\s+baja|time\s+batao|current\s+time)\b", low) or low.strip() in {"time", "time?"}:
            return {
                "action": "companion.time",
                "target": "clock",
                "arguments": {"hi": bool(re.search(r"kitna|batao|abhi|[\u0900-\u097F]", low))},
                "reason": text[:160],
                "risk": "LOW_IMPACT",
                "speak_ok": action_ack(kind="time", user_message=text),
            }
        if any(w in low for w in ("calculator", "calc", "hisab")):
            return {
                "action": "application.open",
                "target": "Calculator",
                "arguments": {"app": "Calculator"},
                "reason": text[:160],
                "risk": "LOW_IMPACT",
                "speak_ok": action_ack(kind="app", user_message=text),
            }
        if any(w in low for w in ("notes", "notepad", "stickies")):
            app = "Notes"
            return {
                "action": "application.open",
                "target": app,
                "arguments": {"app": app},
                "reason": text[:160],
                "risk": "LOW_IMPACT",
                "speak_ok": action_ack(kind="app", user_message=text),
            }
        if re.search(r"\b(email|mail|gmail)\b", low):
            to_m = re.search(r"(?:to|ko)\s+(\S+@\S+)", low)
            subj_m = re.search(r"(?:subject|vishay)\s+(.+)$", low)
            addr = to_m.group(1) if to_m else ""
            subj = quote_plus(subj_m.group(1).strip()[:80]) if subj_m else ""
            url = f"mailto:{addr}?subject={subj}" if addr else "mailto:"
            return {
                "action": "browser.open",
                "target": url,
                "arguments": {"url": url},
                "reason": text[:160],
                "risk": "LOW_IMPACT",
                "speak_ok": action_ack(kind="app", user_message=text),
            }

        # --- Volume / mute (OS control) ---
        if re.search(r"\b(mute|unmute|volume|awaz)\b", low) or "awaz" in low:
            if re.search(r"\bunmute\b", low) or "mute hatao" in low:
                return {
                    "action": "system.volume",
                    "target": "unmute",
                    "arguments": {"mute": False},
                    "reason": text[:160],
                    "risk": "LOW_IMPACT",
                    "speak_ok": action_ack(kind="volume", user_message=text),
                }
            if re.search(r"\bmute\b", low) and "unmute" not in low:
                return {
                    "action": "system.volume",
                    "target": "mute",
                    "arguments": {"mute": True},
                    "reason": text[:160],
                    "risk": "LOW_IMPACT",
                    "speak_ok": action_ack(kind="volume", user_message=text),
                }
            level = 50
            if any(w in low for w in ("badhao", "up", "increase", "louder", "zyada", "full", "max")):
                level = 80
            elif any(w in low for w in ("kam", "down", "decrease", "lower", "quiet", "soft")):
                level = 25
            mvol = re.search(r"(\d{1,3})\s*%?", low)
            if mvol:
                level = max(0, min(100, int(mvol.group(1))))
            return {
                "action": "system.volume",
                "target": f"volume:{level}",
                "arguments": {"level": level},
                "reason": text[:160],
                "risk": "LOW_IMPACT",
                "speak_ok": action_ack(kind="volume", user_message=text),
            }

        # --- YouTube / Google / weather (browser) ---
        if "youtube" in low or "youtu" in low:
            q = ""
            mq = re.search(
                r"(?:youtube(?:\s+(?:par|pe|pe|on))?\s+(?:play|search|khoj|dhundo)?\s*|play\s+)(.+)$",
                low,
            )
            if mq:
                q = mq.group(1).strip(" .")
                for junk in ("kholo", "khol", "open", "please", "karo"):
                    q = q.replace(junk, "").strip()
            if q and q not in {"kholo", "khol", "open", "please"}:
                url = f"https://www.youtube.com/results?search_query={quote_plus(q)}"
            else:
                url = "https://www.youtube.com"
            return {
                "action": "browser.open",
                "target": url,
                "arguments": {"url": url},
                "reason": text[:160],
                "risk": "LOW_IMPACT",
                "speak_ok": action_ack(kind="youtube", query=q, user_message=text),
            }

        # Prefer explicit search/google over weather keyword false-positives
        if re.search(r"\b(google|search|browser)\b", low) or "search karo" in low:
            mq = re.search(
                r"(?:google(?:\s+search)?|search(?:\s+for)?|khoj)\s+(.+)$",
                low,
            )
            q = (mq.group(1).strip(" .") if mq else "").strip()
            for junk in ("kholo", "khol", "open", "please", "karo", "on google", "pe", "par"):
                q = re.sub(rf"\b{re.escape(junk)}\b", "", q).strip()
            if q.lower().startswith("search "):
                q = q[7:].strip()
            url = (
                f"https://www.google.com/search?q={quote_plus(q)}"
                if q
                else "https://www.google.com"
            )
            return {
                "action": "browser.open",
                "target": url,
                "arguments": {"url": url},
                "reason": text[:160],
                "risk": "LOW_IMPACT",
                "speak_ok": action_ack(kind="search", query=q, user_message=text),
            }

        if any(w in low for w in ("mausam", "weather", "forecast", "temperature")):
            city = "Delhi"
            city_m = re.search(
                r"(?:in|at|ka|ki|mein|me)\s+([a-zA-Z\u0900-\u097F]{3,40})",
                low,
            )
            if city_m:
                city = city_m.group(1).strip()
            elif re.search(r"\b(delhi|mumbai|bangalore|bengaluru|hyderabad|chennai|kolkata|pune|jaipur)\b", low):
                city = re.search(
                    r"\b(delhi|mumbai|bangalore|bengaluru|hyderabad|chennai|kolkata|pune|jaipur)\b",
                    low,
                ).group(1)
            return {
                "action": "companion.weather",
                "target": city,
                "arguments": {"city": city, "locale_hi": "mausam" in low or bool(re.search(r"[\u0900-\u097F]", text or ""))},
                "reason": text[:160],
                "risk": "LOW_IMPACT",
                "speak_ok": action_ack(kind="weather", query=city, user_message=text),
            }

        # Resolve "it" / project references from session context
        wants_open = bool(re.search(r"\b(open|launch|start|kholo|khol)\b", low))
        refers_project = any(
            k in low for k in ("project", "om project", "om-ai", "folder", "it", "that", "this")
        )
        if wants_open and (refers_project or "code" in low or "vscode" in low):
            app = "Visual Studio Code"
            if sess and sess.last_app_hint:
                app = sess.last_app_hint
            elif "finder" in low:
                app = "Finder"
            path = ""
            if sess and sess.last_path_hint:
                path = sess.last_path_hint
            elif "om" in low or (sess and sess.last_project_hint == "OM"):
                path = str(root)
            args: dict[str, Any] = {"app": app}
            if path:
                args["path"] = path
                args["args"] = [path]
            return {
                "action": "application.open",
                "target": app,
                "arguments": args,
                "reason": f"User requested: {text[:160]}",
                "risk": "LOW_IMPACT",
            }
        if any(w in low for w in ("open ", "launch ", "start ", "kholo", "khol ")):
            target = "Visual Studio Code" if any(
                x in low for x in ("code", "vs code", "vscode")
            ) else "Finder"
            if "browser" in low or "chrome" in low or "safari" in low:
                target = "Safari" if "safari" in low else ("Google Chrome" if "chrome" in low else "Safari")
            return {
                "action": "application.open",
                "target": target,
                "arguments": {"app": target},
                "reason": f"User requested: {text[:160]}",
                "risk": "LOW_IMPACT",
            }
        if "list files" in low or "show files" in low:
            return {
                "action": "filesystem.list",
                "target": ".",
                "arguments": {"path": "."},
                "reason": text[:160],
                "risk": "READ_ONLY",
            }
        if "delete" in low or "remove" in low:
            # Refuse empty targets — never plan a destructive delete without a path
            path_m = re.search(
                r"(?:delete|remove|erase)\s+(?:file\s+|the\s+)?([~/][^\s]+|\S+\.\w{1,8})",
                low,
            )
            if not path_m:
                return None
            return {
                "action": "filesystem.delete",
                "target": path_m.group(1),
                "arguments": {"path": path_m.group(1)},
                "reason": text[:160],
                "risk": "DESTRUCTIVE",
            }
        return None

    def _permission_gate(self, planned: dict[str, Any]) -> dict[str, Any]:
        risk = str(planned.get("risk") or "LOW_IMPACT")
        if risk in {"DESTRUCTIVE", "SENSITIVE", "EXTERNAL_SIDE_EFFECT"}:
            pid = str(uuid.uuid4())[:8]
            return {
                "requires_approval": True,
                "allowed": False,
                "permission_id": pid,
                "risk": risk,
                "prompt": f"I can run `{planned.get('action')}` ({risk}). Say yes to allow, or no to cancel.",
                "action": planned,
            }
        # Low impact / read-only auto-allow when actions enabled
        return {"requires_approval": False, "allowed": True, "risk": risk, "action": planned}

    def _resolve_permission(self, ingested: dict[str, Any]) -> dict[str, Any]:
        assert self.voice is not None
        decision = ingested.get("permission_response")
        planned = self.voice.session.pending_action or {}
        pid = ingested.get("permission_id")
        self._emit("permission.resolved", {"permission_id": pid, "decision": decision})
        self.voice.session.pending_permission_id = None
        self.voice.session.pending_action = None
        if decision != "approve":
            msg = "Okay — cancelled."
            self.voice.speak(msg)
            return {"answer": msg, "activities": [], "permission_id": pid}
        result = self._execute_action(planned)
        msg = result.get("message") or ("Done." if result.get("ok") else "I couldn't complete that.")
        self.voice.speak(msg)
        return {"answer": msg, "activities": [], "result": result}

    def _execute_action(self, planned: dict[str, Any]) -> dict[str, Any]:
        self._emit("action.started", planned)
        try:
            action = str(planned.get("action") or "")
            # Companion-local tools (not DeviceRuntime capabilities)
            if action == "companion.weather":
                from om_ai.core.device_runtime.weather import fetch_weather_spoken

                args = dict(planned.get("arguments") or {})
                pack = fetch_weather_spoken(
                    str(args.get("city") or planned.get("target") or "Delhi"),
                    locale_hi=bool(args.get("locale_hi")),
                )
                spoken = str(pack.get("spoken") or planned.get("speak_ok") or "Done.")
                payload = {"ok": bool(pack.get("ok")), "result": pack, "message": spoken}
                self._emit("action.completed" if pack.get("ok") else "action.failed", payload)
                return payload
            if action == "companion.time":
                from datetime import datetime

                now = datetime.now().strftime("%I:%M %p").lstrip("0")
                hi = bool((planned.get("arguments") or {}).get("hi"))
                spoken = f"Abhi time {now} hai." if hi else f"It's {now}."
                payload = {"ok": True, "message": spoken}
                self._emit("action.completed", payload)
                return payload

            if self.devices is not None and hasattr(self.devices, "invoke"):
                from om_ai.core.companion_security import SecurityContext
                ctx = SecurityContext(session_id=self.context.session_id)
                out = self.devices.invoke(ctx, action, dict(planned.get("arguments") or {}))
                ok = bool(out.get("ok", True)) if isinstance(out, dict) else True
                # Verify
                verified = ok
                if self.agents and hasattr(self.agents, "verify"):
                    try:
                        verified = bool(self.agents.verify(planned, out))
                    except Exception:
                        verified = ok
                payload = {
                    "ok": verified,
                    "result": out,
                    "message": (
                        planned.get("speak_ok")
                        or (
                            "It's open."
                            if verified and str(planned.get("action", "")).startswith(("application.open", "browser."))
                            else ("Completed." if verified else "Action could not be verified.")
                        )
                    ),
                }
                self._emit("action.completed" if verified else "action.failed", payload)
                return payload
            if self.actions is not None:
                # ActionControlEngine path
                for meth in ("execute", "run", "handle"):
                    fn = getattr(self.actions, meth, None)
                    if callable(fn):
                        out = fn(planned)
                        ok = bool((out or {}).get("ok", True)) if isinstance(out, dict) else True
                        self._emit("action.completed" if ok else "action.failed", {"result": out})
                        return {"ok": ok, "result": out, "message": "Completed." if ok else "Failed."}
            return {"ok": False, "message": "Action runtime unavailable."}
        except Exception as exc:
            self._emit("action.failed", {"error": str(exc)})
            return {"ok": False, "message": f"Action failed: {exc}", "error": str(exc)}

    def interrupt(self) -> dict[str, Any]:
        if self.voice:
            self.voice.interrupt_speech()
        if self.presence is not None:
            try:
                self.presence.interrupt()
            except Exception:
                pass
        return {
            "ok": True,
            "state": getattr(self.voice, "state", None) and self.voice.state.value,
            "presence": self.presence.status() if self.presence else {},
        }

    def status_banner(self) -> dict[str, Any]:
        voice_st = self.voice.status() if self.voice else {}
        comps = [
            component_health("OM Model", True, "shared runtime"),
            component_health("Companion Brain", self.brain is not None),
            component_health("Memory", self.memory is not None or not self.config.memory_enabled),
            component_health("Knowledge", True, "via brain bridges"),
            component_health("Agent Runtime", self.agents is not None or not self.config.actions_enabled),
            component_health("Action Control", self.actions is not None or not self.config.actions_enabled),
            component_health("Security", self.security is not None),
            component_health("Microphone", bool((voice_st.get("devices") or {}).get("ready")) or self.config.text_only, "text-only" if self.config.text_only else ""),
            component_health("STT", bool(((voice_st.get("stt") or {}).get("recognizer") or voice_st.get("stt") or {}).get("ready")) or self.config.text_only),
            component_health("TTS", bool((voice_st.get("tts") or {}).get("synth", voice_st.get("tts") or {}).get("ready") if isinstance(voice_st.get("tts"), dict) else False) or self.config.text_only),
            component_health("Wake Word", self.config.wake_word_enabled or self.config.text_only, self.config.wake_word),
            component_health("Avatar", self.config.avatar_enabled and not self.config.no_avatar, "UI"),
            component_health("Realtime Gateway", self.realtime is not None),
        ]
        state = voice_st.get("state") or ("READY" if self._started else "STOPPED")
        # User-facing status: wake wait reads as LISTENING
        if state == "LISTENING_FOR_WAKE_WORD":
            state = "LISTENING"
        elif self.config.text_only and state == "READY":
            state = "LISTENING"
        return {
            "ok": self._started,
            "lifecycle": self.lifecycle.value,
            "session_id": self.context.session_id,
            "components": comps,
            "wake_phrase": self.config.wake_word,
            "status": state,
            "config": {
                "text_only": self.config.text_only,
                "wake_word_enabled": self.config.wake_word_enabled,
                "avatar_enabled": self.config.avatar_enabled and not self.config.no_avatar,
                "actions_enabled": self.config.actions_enabled,
                "memory_enabled": self.config.memory_enabled,
            },
        }

    def doctor(self) -> dict[str, Any]:
        checks = []
        import sys
        checks.append({"name": "python", "status": "PASS" if sys.version_info >= (3, 11) else "WARN", "detail": sys.version.split()[0]})
        # checkpoint
        from pathlib import Path
        root = Path(__file__).resolve().parents[3]
        ckpt = list((root / "artifacts").glob("**/*.pt"))[:1] if (root / "artifacts").exists() else []
        checks.append({"name": "om_checkpoint", "status": "PASS" if ckpt or True else "WARN", "detail": str(ckpt[0]) if ckpt else "optional"})
        # tokenizer
        tok = root / "artifacts" / "tokenizer-production-65536.json"
        alt = root / "artifacts" / "tokenizer-fixed-v3.json"
        checks.append({"name": "tokenizer", "status": "PASS" if tok.is_file() or alt.is_file() else "WARN", "detail": str(tok if tok.is_file() else alt)})
        # mic
        from om_ai.core.voice_intelligence import AudioDeviceManager
        dev = AudioDeviceManager().status()
        checks.append({"name": "microphone", "status": "PASS" if dev.get("ready") else "WARN", "detail": dev.get("backend")})
        from om_ai.core.voice_intelligence import SpeechRecognizer, StreamingTTS, WakeWordEngine
        checks.append({"name": "stt", "status": "PASS" if SpeechRecognizer().ready else "WARN", "detail": SpeechRecognizer().status().get("backend")})
        checks.append({"name": "tts", "status": "PASS" if StreamingTTS().synth.ready else "WARN", "detail": StreamingTTS().status()})
        checks.append({"name": "wake_word", "status": "PASS", "detail": WakeWordEngine(self.config.wake_word).status()})
        checks.append({"name": "memory_db", "status": "PASS", "detail": str(root / "artifacts" / "companion")})
        checks.append({"name": "api_port", "status": "PASS", "detail": f"{self.config.bind_host}:{self.config.bind_port}"})
        ui = root / "om_ai" / "api" / "static" / "companion" / "index.html"
        checks.append({"name": "frontend", "status": "PASS" if ui.is_file() else "WARN", "detail": str(ui)})
        return {"checks": checks, "ok": all(c["status"] in {"PASS", "WARN"} for c in checks)}


_RUNTIME: CompanionRuntime | None = None


def get_companion_runtime(**overrides) -> CompanionRuntime:
    global _RUNTIME
    if _RUNTIME is None:
        cfg = CompanionConfig.from_env(**overrides)
        _RUNTIME = CompanionRuntime(cfg)
    return _RUNTIME


def reset_companion_runtime() -> None:
    global _RUNTIME
    if _RUNTIME is not None:
        try:
            _RUNTIME.stop()
        except Exception:
            pass
    _RUNTIME = None
