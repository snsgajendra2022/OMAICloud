"""Companion API routes — voice-first companion + brain/actions."""
from __future__ import annotations

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/companion", tags=["companion"])


class MessageBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)
    history: list[dict[str, Any]] | None = None
    session_id: str | None = None
    speak: bool = True


class SessionBody(BaseModel):
    """Optional session bootstrap payload from the companion UI."""

    display_name: str | None = None
    language: str | None = None
    purpose: str | None = None
    actor: str | None = None
    tenant_id: str | None = None


class DeviceBody(BaseModel):
    input_device_id: int


class SpeakBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


def _runtime():
    from om_ai.core.companion_runtime import get_companion_runtime

    return get_companion_runtime()


def _ensure_browser_session():
    """Browser companion: continuous talk, no wake-word gate every turn."""
    rt = _runtime()
    if not rt._started:
        rt.config.text_only = True
        rt.config.wake_word_enabled = False
        rt.start()
    else:
        rt.config.wake_word_enabled = False
        if rt.voice is not None:
            rt.voice.wake_word_enabled = False
            try:
                rt.voice.session.activate()
            except Exception:
                pass
    return rt


def _load_user_context(
    *,
    actor: str = "",
    display_name: str = "",
    language: str = "",
    purpose: str = "",
) -> dict[str, Any]:
    """Merge onboarding + request hints into a live user context (no static defaults as identity)."""
    ctx: dict[str, Any] = {
        "name": (display_name or "").strip(),
        "language": (language or "").strip() or "auto",
        "purpose": (purpose or "").strip() or "general",
        "actor": (actor or "").strip(),
    }
    try:
        from om_ai.core.onboarding import get_onboarding_engine

        eng = get_onboarding_engine()
        pack = eng.load(actor) if actor else None
        if not pack:
            # Fall back to most recent onboarding file if single-user desktop
            store = getattr(eng, "store_dir", None)
            if store and store.is_dir():
                files = sorted(store.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
                if files:
                    import json

                    pack = json.loads(files[0].read_text(encoding="utf-8"))
        if pack:
            profile = pack.get("user_profile") or {}
            assistant = pack.get("assistant") or {}
            memory = pack.get("memory") or {}
            ctx["name"] = ctx["name"] or str(profile.get("display_name") or "")
            ctx["language"] = (
                language
                or str(profile.get("language") or "")
                or ctx["language"]
            )
            ctx["purpose"] = purpose or str(profile.get("purpose") or ctx["purpose"])
            ctx["style"] = str(profile.get("response_style") or profile.get("style") or "")
            ctx["assistant_name"] = str(assistant.get("name") or "OM")
            ctx["memory_likes"] = list(memory.get("likes") or [])
            ctx["onboarding"] = profile
    except Exception as exc:
        logger.debug("onboarding context: %s", exc)

    if not ctx["name"]:
        ctx["name"] = "Sir"
    return ctx


def _dynamic_greeting(user_ctx: dict[str, Any]) -> str:
    """Build greeting from time + profile + personality — never a fixed canned script."""
    name = str(user_ctx.get("name") or "Sir")
    language = str(user_ctx.get("language") or "en")
    purpose = str(user_ctx.get("purpose") or "general")
    style = str(user_ctx.get("style") or "")
    hour = datetime.now().hour
    if hour < 12:
        daypart_en, daypart_hi = "Good morning", "Good morning"
    elif hour < 17:
        daypart_en, daypart_hi = "Good afternoon", "Good afternoon"
    else:
        daypart_en, daypart_hi = "Good evening", "Good evening"

    # Prefer voice-presence personality prompt shaping via a short spoken line from style rules
    try:
        from om_ai.core.companion_personality.voice_presence import get_voice_presence

        vp = get_voice_presence()
        locale = "hi" if str(language).lower() in {"hi", "hi-en", "hinglish"} else "en"
        # Ask style layer to adapt a brain-shaped seed (not a keyword chatbot reply)
        seed = (
            f"{daypart_hi} {name}. Main OM hoon — hazir hoon. Aaj {purpose} pe kaam karein?"
            if locale == "hi"
            else f"{daypart_en} {name}. I am OM — ready. Shall we continue with {purpose}?"
        )
        if style:
            seed = (
                f"{daypart_hi} {name}. Main OM hoon. Aap {style} style pasand karte ho — boliye kahan se shuru karein?"
                if locale == "hi"
                else f"{daypart_en} {name}. I am OM. I'll keep things {style}. Where shall we begin?"
            )
        pack = vp.analyze("hello", seed, context={"locale": locale, "onboarding": user_ctx.get("onboarding") or {}})
        return str(pack.get("spoken") or seed)
    except Exception:
        if str(language).lower() in {"hi", "hi-en", "hinglish"}:
            return f"{daypart_hi} {name}. Main OM hoon — ready. Boliye."
        return f"{daypart_en} {name}. I am OM — ready. What shall we take on?"


@router.get("/status")
def companion_status() -> dict[str, Any]:
    rt = _runtime()
    if not rt._started:
        return {"started": False, **rt.status_banner()}
    return {"started": True, **rt.status_banner()}


@router.post("/session")
def companion_session(body: SessionBody | None = None) -> dict[str, Any]:
    """
    Start OM Companion session (dynamic).

    Accepts empty `{}` or optional profile fields. Builds greeting from
    onboarding + time-of-day + voice presence — not static internal copy.
    """
    try:
        payload = body or SessionBody()

        rt = _ensure_browser_session()
        session_id = rt.context.session_id

        user_ctx = _load_user_context(
            actor=str(payload.actor or ""),
            display_name=str(payload.display_name or ""),
            language=str(payload.language or ""),
            purpose=str(payload.purpose or ""),
        )

        # Persist live context on runtime
        rt.context.meta["user_context"] = user_ctx
        rt.context.meta["session_started"] = True
        rt.context.meta["mode"] = "voice_conversation"
        rt.onboarding_context = {
            "user": user_ctx.get("onboarding") or user_ctx,
            "assistant": {"name": user_ctx.get("assistant_name") or "OM"},
            "memory": {"likes": user_ctx.get("memory_likes") or []},
        }

        voice_state: dict[str, Any] = {"status": "ready"}
        try:
            if rt.voice is not None and hasattr(rt.voice, "start_listening"):
                voice_state = rt.voice.start_listening() or voice_state
            elif rt.voice is not None:
                voice_state = {"status": "ready", "wake_word": False}
        except Exception as exc:
            voice_state = {"status": "ready", "note": str(exc)}

        greeting = _dynamic_greeting(user_ctx)
        spoken_tts = greeting
        try:
            from om_ai.core.companion_personality.voice_presence import shape_for_speech

            pack = shape_for_speech(greeting, user_message="hello")
            greeting = str(pack.get("spoken") or greeting)
            spoken_tts = str(pack.get("spoken_tts") or greeting)
        except Exception:
            pass

        return {
            "ok": True,
            "success": True,
            "session_id": session_id,
            "status": rt.status_banner() if hasattr(rt, "status_banner") else {"started": True},
            "mode": "voice_conversation",
            "voice": {
                "enabled": True,
                "listening": True,
                "state": voice_state,
            },
            "language": user_ctx.get("language") or "auto",
            "user": {
                "name": user_ctx.get("name"),
                "purpose": user_ctx.get("purpose"),
                "style": user_ctx.get("style"),
            },
            "greeting": greeting,
            "spoken": greeting,
            "spoken_tts": spoken_tts,
            "memory_line": (
                f"Working on {user_ctx.get('purpose')}"
                if user_ctx.get("purpose")
                else "Companion ready"
            ),
            "capabilities": [
                "conversation",
                "memory",
                "voice",
                "reasoning",
                "actions",
                "knowledge",
            ],
        }
    except Exception as exc:
        logger.exception("Companion session failed")
        return {"ok": False, "success": False, "error": str(exc)}

@router.post("/message")
def companion_message(body: MessageBody) -> dict[str, Any]:
    rt = _ensure_browser_session()
    out = rt.handle_text(body.text, history=body.history)
    # Prefer browser TTS for lip-sync + no double-speak from macOS say on server
    if rt.voice is not None:
        try:
            rt.voice.interrupt_speech()
        except Exception:
            pass
    out["speak_client"] = True
    out["session_id"] = rt.context.session_id
    return out


@router.post("/interrupt")
def companion_interrupt() -> dict[str, Any]:
    return _runtime().interrupt()


@router.post("/mute")
def companion_mute() -> dict[str, Any]:
    rt = _runtime()
    if rt.voice:
        rt.voice.mute()
    return {"ok": True, "muted": True}


@router.post("/unmute")
def companion_unmute() -> dict[str, Any]:
    rt = _runtime()
    if rt.voice:
        rt.voice.unmute()
    return {"ok": True, "muted": False}


@router.post("/tts")
def companion_tts(body: SpeakBody):
    """Synthesize natural speech audio for the avatar (Jarvis-like voice)."""
    from starlette.background import BackgroundTask

    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty")

    # Pace / neural path via Voice Engine when available
    spoken = text
    try:
        from om_ai.core.voice_engine import get_voice_engine

        ve = get_voice_engine()
        plan = ve.speak_plan(text, emotion="calm", presence="speaking")
        spoken = str(plan.get("text") or text)
        if "[[slnc" not in text.lower() and "[[slnc" in spoken.lower():
            pass
        elif "[[slnc" in text.lower():
            spoken = text
        else:
            from om_ai.core.companion_personality.voice_presence import shape_for_speech

            spoken = shape_for_speech(text).get("spoken_tts") or spoken
    except Exception:
        from om_ai.core.companion_personality.voice_presence import shape_for_speech

        spoken = shape_for_speech(text).get("spoken_tts") or text

    fd, name = tempfile.mkstemp(suffix=".wav")
    import os

    os.close(fd)
    tmp = Path(name)

    def _cleanup() -> None:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass

    try:
        # Prefer neural TTS when configured
        try:
            from om_ai.core.voice_engine import get_voice_engine

            neural = get_voice_engine().synthesize(spoken, output_path=tmp.with_suffix(".mp3"))
            if neural.get("ok"):
                path = Path(str(neural.get("path") or tmp))
                media = "audio/mpeg" if path.suffix.lower() == ".mp3" else "audio/wav"

                def _cleanup_path() -> None:
                    try:
                        path.unlink(missing_ok=True)
                    except Exception:
                        pass

                return FileResponse(
                    path=str(path),
                    media_type=media,
                    filename=path.name,
                    background=BackgroundTask(_cleanup_path),
                    headers={
                        "X-OM-Voice": str(neural.get("voice") or "neural"),
                        "X-OM-TTS-Backend": str(neural.get("backend") or "neural"),
                    },
                )
        except Exception:
            pass

        from om_ai.core.voice_intelligence.speech_synthesizer import SpeechSynthesizer

        synth = SpeechSynthesizer()
        result = synth.synthesize(spoken, output_path=tmp)
        path = Path(str(result.get("path") or tmp))
        if not result.get("ok") or not path.is_file() or path.stat().st_size < 44:
            _cleanup()
            raise HTTPException(status_code=501, detail="tts_unavailable")

        def _cleanup_path() -> None:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass

        media = "audio/wav" if path.suffix.lower() == ".wav" else "audio/aiff"
        return FileResponse(
            path=str(path),
            media_type=media,
            filename=path.name,
            background=BackgroundTask(_cleanup_path),
            headers={
                "X-OM-Voice": str(result.get("voice") or ""),
                "X-OM-TTS-Backend": str(result.get("backend") or ""),
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        _cleanup()
        logger.warning("tts endpoint failed: %s", exc)
        raise HTTPException(status_code=501, detail=str(exc)) from exc


@router.post("/hear")
async def companion_hear(audio: UploadFile = File(...)) -> dict[str, Any]:
    """Upload mic audio → STT → companion brain → spoken reply payload."""
    import numpy as np

    from om_ai.core.voice_intelligence.speech_recognizer import SpeechRecognizer

    rt = _ensure_browser_session()
    raw = await audio.read()
    if not raw:
        raise HTTPException(status_code=400, detail="empty_audio")

    # Write temp and let recognizer backends that need files use path;
    # also try numpy decode for wav.
    suffix = Path(audio.filename or "clip.webm").suffix or ".webm"
    tmp = Path(tempfile.mkstemp(suffix=suffix)[1])
    tmp.write_bytes(raw)

    recognizer = SpeechRecognizer()
    text = ""
    stt_meta: dict[str, Any] = {"backend": recognizer.status().get("backend")}
    try:
        if suffix.lower() in {".wav", ".wave"} and recognizer.ready:
            import wave

            with wave.open(str(tmp), "rb") as wf:
                sr = wf.getframerate()
                frames = wf.readframes(wf.getnframes())
                audio_arr = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            pack = recognizer.transcribe_array(audio_arr, sample_rate=sr)
            text = str(pack.get("text") or "").strip()
            stt_meta.update(pack)
        elif recognizer.ready and hasattr(recognizer, "transcribe_file"):
            pack = recognizer.transcribe_file(str(tmp))  # type: ignore[attr-defined]
            text = str(pack.get("text") or "").strip()
            stt_meta.update(pack if isinstance(pack, dict) else {})
        else:
            # Faster-whisper can take path via whisper path
            if recognizer._backend == "faster_whisper" and recognizer._model is not None:
                segments, info = recognizer._model.transcribe(str(tmp), vad_filter=True)
                parts = [s.text.strip() for s in segments if getattr(s, "text", None)]
                text = " ".join(parts).strip()
                stt_meta["language"] = getattr(info, "language", None)
            elif recognizer._backend == "whisper" and recognizer._model is not None:
                pack = recognizer._model.transcribe(str(tmp))
                text = str(pack.get("text") or "").strip()
    except Exception as exc:
        logger.warning("hear STT failed: %s", exc)
        stt_meta["error"] = str(exc)
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass

    if not text:
        return {
            "ok": False,
            "answer": "I couldn't catch that — say it again?",
            "transcript": "",
            "stt": stt_meta,
            "speak_client": True,
            "activities": ["Listening"],
        }

    out = rt.handle_text(text)
    if rt.voice is not None:
        try:
            rt.voice.interrupt_speech()
        except Exception:
            pass
    out["ok"] = True
    out["transcript"] = text
    out["stt"] = stt_meta
    out["speak_client"] = True
    out["session_id"] = rt.context.session_id
    return out


@router.get("/devices")
def companion_devices() -> dict[str, Any]:
    from om_ai.core.voice_intelligence import AudioDeviceManager

    return AudioDeviceManager().status()


@router.post("/device")
def companion_select_device(body: DeviceBody) -> dict[str, Any]:
    from om_ai.core.voice_intelligence import AudioDeviceManager

    return AudioDeviceManager().select_input(body.input_device_id)


@router.get("/permissions")
def companion_permissions() -> dict[str, Any]:
    rt = _runtime()
    pending = None
    if rt.voice and rt.voice.session.pending_permission_id:
        pending = {
            "permission_id": rt.voice.session.pending_permission_id,
            "action": rt.voice.session.pending_action,
        }
    return {"pending": pending}


@router.post("/permissions/{permission_id}/approve")
def companion_approve(permission_id: str) -> dict[str, Any]:
    rt = _runtime()
    if not rt.voice or rt.voice.session.pending_permission_id != permission_id:
        raise HTTPException(status_code=404, detail="permission_not_found")
    return rt.handle_text("yes")


@router.post("/permissions/{permission_id}/deny")
def companion_deny(permission_id: str) -> dict[str, Any]:
    rt = _runtime()
    if not rt.voice or rt.voice.session.pending_permission_id != permission_id:
        raise HTTPException(status_code=404, detail="permission_not_found")
    return rt.handle_text("no")


@router.get("/memory")
def companion_memory() -> dict[str, Any]:
    rt = _runtime()
    mem = rt.memory
    if mem is None:
        try:
            from om_ai.core.companion_memory import MemoryService

            mem = MemoryService()
        except Exception as exc:
            return {"error": str(exc)}
    if hasattr(mem, "list_all"):
        return mem.list_all()
    if hasattr(mem, "snapshot"):
        return mem.snapshot()
    return {"memory": str(mem)}


@router.websocket("/ws/{session_id}")
async def companion_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    rt = _ensure_browser_session()
    if rt.realtime is not None:
        try:
            rt.realtime.streams.hub.register(session_id, websocket)
        except Exception:
            pass
    try:
        await websocket.send_json(
            {
                "event_type": "companion.state",
                "session_id": session_id,
                "payload": {"state": rt.status_banner().get("status")},
            }
        )
        while True:
            data = await websocket.receive_json()
            if not isinstance(data, dict):
                continue
            typ = str(data.get("type") or data.get("event_type") or "")
            if typ in {"message", "user.message"}:
                text = str(data.get("text") or data.get("payload", {}).get("text") or "")
                out = rt.handle_text(text)
                out["speak_client"] = True
                await websocket.send_json(
                    {
                        "event_type": "response.delta",
                        "session_id": session_id,
                        "payload": out,
                    }
                )
            elif typ == "interrupt":
                await websocket.send_json(
                    {"event_type": "voice.interrupted", "payload": rt.interrupt()}
                )
            elif typ == "ping":
                await websocket.send_json({"event_type": "pong", "payload": {}})
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("companion ws closed: %s", exc)
    finally:
        if rt.realtime is not None:
            try:
                rt.realtime.streams.hub.unregister(session_id, websocket)
            except Exception:
                pass
