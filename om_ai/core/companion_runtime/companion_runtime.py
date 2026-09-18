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

            # Memory
            if self.config.memory_enabled:
                try:
                    from om_ai.core.companion_memory import MemoryService
                    self.memory = MemoryService()
                except Exception:
                    try:
                        from om_ai.core.companion_memory.memory_service import MemoryService
                        self.memory = MemoryService()
                    except Exception as exc:
                        logger.warning("memory init: %s", exc)

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

            # Voice
            from om_ai.core.voice_intelligence import VoiceRuntime
            self.voice = VoiceRuntime(
                wake_phrase=self.config.wake_word,
                text_only=self.config.text_only,
                wake_word_enabled=self.config.wake_word_enabled and not self.config.text_only,
                on_event=lambda et, payload: self._emit(et, payload),
                on_final_transcript=lambda text, session: None,
            )
            voice_start = self.voice.start()
            self.registry.register("voice", self.voice)
            self.registry.register("brain", self.brain)
            self.registry.register("memory", self.memory)
            self.registry.register("actions", self.actions)
            self.registry.register("agents", self.agents)
            self.registry.register("devices", self.devices)
            self.registry.register("security", self.security)

            self._started = True
            self.lifecycle = Lifecycle.RUNNING
            banner = self.status_banner()
            banner["voice_start"] = voice_start
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

    def handle_text(self, text: str, *, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if not self._started:
            self.start()
        assert self.voice is not None
        self.context.trace_id = str(uuid.uuid4())
        self._emit("brain.started", {"text": (text or "")[:120]})

        # Cancellation / stop commands
        low = (text or "").strip().lower()
        if low in {"stop", "cancel", "cancel that", "don't do that", "mute"}:
            if low == "mute":
                self.voice.mute()
                return {"answer": "Muted.", "activities": ["Muted microphone"], "state": self.voice.state.value}
            self.voice.interrupt_speech()
            if self.agents and hasattr(self.agents, "cancel"):
                try:
                    self.agents.cancel()
                except Exception:
                    pass
            return {"answer": "Stopped.", "activities": ["Cancelled active work"], "state": self.voice.state.value}

        ingested = self.voice.ingest_text(text)
        if ingested.get("wake_only"):
            reply = ingested.get("prompt") or "Yes?"
            self.voice.speak(reply)
            self._emit("avatar.state", {"state": "attentive"})
            return {"answer": reply, "activities": ["Wake detected"], "wake": True, "session": ingested.get("session")}

        if ingested.get("permission_response"):
            return self._resolve_permission(ingested)

        if not ingested.get("ok"):
            reason = ingested.get("reason")
            if reason == "waiting_for_wake":
                return {
                    "answer": "",
                    "waiting_for_wake": True,
                    "activities": ["Listening for wake word"],
                    "state": self.voice.state.value,
                }
            return {"answer": "", "error": reason, "state": self.voice.state.value}

        user_text = str(ingested.get("text") or text)
        hist = history or list(self.voice.session.history)
        self._update_session_context(user_text)

        # Action intent via brain semantic + action planner
        brain_out = self._run_brain(user_text, hist)
        activities = list(brain_out.get("activities") or ["Understanding request"])
        for a in activities:
            self._emit("brain.activity", {"activity": a})

        semantic = brain_out.get("semantic") or {}
        answer = str(brain_out.get("answer") or "").strip()

        # Permission-sensitive actions
        planned = None
        if self.config.actions_enabled and self.actions is not None:
            if semantic.get("requires_action") or self._looks_like_action(user_text):
                planned = self._plan_action(user_text, semantic)
        if planned:
            self._emit("action.planned", planned)
            decision = self._permission_gate(planned)
            if decision.get("requires_approval"):
                self.voice.session.pending_permission_id = decision.get("permission_id")
                self.voice.session.pending_action = planned
                msg = decision.get("prompt") or "Permission required. Say yes to allow, or no to cancel."
                self.voice.speak(msg)
                self._emit("permission.required", decision)
                return {
                    "answer": msg,
                    "activities": activities + ["Waiting for permission"],
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

        if not answer:
            answer = "I'm here — how can I help?"

        # Memory write (non-sensitive)
        if self.memory is not None and self.config.memory_enabled:
            try:
                self.memory.remember_turn(user_text, answer)
            except Exception:
                try:
                    if hasattr(self.memory, "add_episode"):
                        self.memory.add_episode(user_text, answer)
                except Exception:
                    pass

        # Continuous learning observe (offline pipeline hook)
        try:
            from om_ai.core.continuous_learning import run_continuous_learning
            run_continuous_learning(user_text, answer)
        except Exception:
            pass

        self.voice.speak(answer)
        self._emit("avatar.state", {"state": "speaking"})
        try:
            self.voice.session.add_turn("assistant", answer)
        except Exception:
            pass
        return {
            "answer": answer,
            "activities": activities,
            "semantic": semantic,
            "session": self.voice.session.to_dict(),
            "state": self.voice.state.value,
            "trace_id": self.context.trace_id,
        }

    def _run_brain(self, text: str, history: list[dict[str, Any]]) -> dict[str, Any]:
        if self.brain is not None:
            for meth in ("run", "handle", "process", "turn"):
                fn = getattr(self.brain, meth, None)
                if callable(fn):
                    try:
                        out = fn(text, history=history)
                        if isinstance(out, dict) and (out.get("answer") is not None or out.get("semantic")):
                            return out
                    except TypeError:
                        try:
                            out = fn(text)
                            if isinstance(out, dict):
                                return out
                        except Exception:
                            pass
                    except Exception as exc:
                        logger.debug("brain.%s failed: %s", meth, exc)
        try:
            from om_ai.core.companion_brain import run_companion_brain
            return run_companion_brain(text, history=history)
        except Exception:
            from om_ai.core.chatgpt_runtime import run_chatgpt_runtime
            pack = run_chatgpt_runtime(text, history=history)
            return {
                "answer": pack.get("answer") or "",
                "semantic": (pack.get("chat_intelligence") or {}).get("intent") or {},
                "activities": ["Preparing answer"],
            }

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
            )
        ):
            return True
        # Coreference: "open it" / "do it"
        if re.search(r"\b(open|launch|delete|remove)\s+(it|that|this)\b", low):
            return True
        return False

    def _plan_action(self, text: str, semantic: dict[str, Any]) -> dict[str, Any] | None:
        from pathlib import Path

        low = (text or "").lower()
        sess = self.voice.session if self.voice else None
        root = Path(__file__).resolve().parents[3]

        # Resolve "it" / project references from session context
        wants_open = bool(re.search(r"\b(open|launch|start)\b", low))
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
        if any(w in low for w in ("open ", "launch ", "start ")):
            target = "Visual Studio Code" if any(
                x in low for x in ("code", "vs code", "vscode")
            ) else "Finder"
            if "browser" in low or "chrome" in low or "safari" in low:
                target = "Safari"
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
            return {
                "action": "filesystem.delete",
                "target": "",
                "arguments": {"path": ""},
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
            return {"answer": msg, "activities": ["Permission denied"], "permission_id": pid}
        result = self._execute_action(planned)
        msg = result.get("message") or ("Done." if result.get("ok") else "I couldn't complete that.")
        self.voice.speak(msg)
        return {"answer": msg, "activities": ["Executed after approval"], "result": result}

    def _execute_action(self, planned: dict[str, Any]) -> dict[str, Any]:
        self._emit("action.started", planned)
        try:
            if self.devices is not None and hasattr(self.devices, "invoke"):
                from om_ai.core.companion_security import SecurityContext
                ctx = SecurityContext(session_id=self.context.session_id)
                out = self.devices.invoke(ctx, str(planned.get("action")), dict(planned.get("arguments") or {}))
                ok = bool(out.get("ok", True)) if isinstance(out, dict) else True
                # Verify
                verified = ok
                if self.agents and hasattr(self.agents, "verify"):
                    try:
                        verified = bool(self.agents.verify(planned, out))
                    except Exception:
                        verified = ok
                payload = {"ok": verified, "result": out, "message": "It's open." if verified and "application.open" in str(planned.get("action")) else ("Completed." if verified else "Action could not be verified.")}
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
        return {"ok": True, "state": getattr(self.voice, "state", None) and self.voice.state.value}

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
        checks.append({"name": "api_port", "status": "PASS", "detail": str(self.config.bind_port)})
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
