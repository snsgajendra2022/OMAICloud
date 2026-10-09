"""Chat reply backends: OM native (default), local engine, or OpenAI-compatible API.

Selection (``OM_AI_CHAT_BACKEND`` or ``OM_MODEL_PROVIDER``):
  - ``om_native`` (default when unset): OMNativeBackend ONLY — no third-party LLM fallback
  - ``openai`` / ``local``: explicit opt-in only
  - ``auto``: OpenAI if API key set → local OM (never Ollama)

Ollama is not part of the production path. Legacy client lives under
``om_ai.legacy.ollama`` and is never auto-imported by serve/API.
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable
from zoneinfo import ZoneInfo

import httpx

from om_ai.backends.base import NativeCheckpointError

logger = logging.getLogger(__name__)
try:
    from om_ai.language import LanguageManager

    _language_manager = LanguageManager()

except Exception:

    _language_manager = None

    logger.debug(
        "Language Intelligence Layer unavailable"
    )
BackendName = str  # "om_native" | "local" | "openai"


class ResponseEcho:
    """Reject answers that merely repeat the user question."""

    @staticmethod
    def check(question: str, answer: str) -> bool:
        import re

        q = re.sub(r"\W+", " ", (question or "").lower()).strip()
        a = re.sub(r"\W+", " ", (answer or "").lower()).strip()
        if not q or not a:
            return False
        if a == q:
            return True
        if q in a and len(a) <= len(q) + 28:
            return True
        if a.startswith("understood ") and q in a and len(a) <= len(q) + 40:
            return True
        return False


_DEFAULT_BACKEND = "om_native"

# Keep identity short: local OM-1.0 configs often use max_seq_len=128, and a long
# system preamble was truncating the user turn and producing empty/garbage replies.
OM_SYSTEM_IDENTITY = (
    "You are OM AI, powered by the OM-1.0 native language model. "
    "Do not claim to be Llama, Ollama, ChatGPT, GPT, Claude, Gemini, "
    "or another third-party model."
)

OM_SYSTEM_IDENTITY_COMPACT = "You are OM AI (OM-1.0 native language model)."

# Old SFT-memorized one-liners — never return these as "final"; re-sample from the model.
_SCRIPT_TEMPLATES = {
    "Hi! I'm OM AI. How can I help you today?",
    "Hi! How can I help you today?",
    "नमस्ते! मैं OM AI हूँ। आज मैं आपकी कैसे मदद कर सकता हूँ?",
    "I'm OM AI, powered by OM-1.0. How can I help?",
    "मैं OM AI हूँ — OM-1.0 मॉडल। आप क्या करना चाहेंगे?",
}


def _looks_scripted(text: str | None) -> bool:
    s = (text or "").strip()
    if not s:
        return False
    if s in _SCRIPT_TEMPLATES:
        return True
    # Near-exact scripted greets from early SFT.
    low = s.lower()
    return bool(
        re.fullmatch(
            r"hi[!.,]?\s+i'?m\s+om\s+ai\.?\s+how\s+can\s+i\s+help\s+you\s+today\??",
            low,
        )
    )


def _latest_user_text(messages: list[dict]) -> str:
    for m in reversed(messages or []):
        if str(m.get("role") or "") == "user":
            text = str(m.get("content") or "").strip()
            # Strip legacy UI tool tags that poison tiny chat-SFT greets.
            for tag in ("[web search enabled]", "[code interpreter enabled]"):
                text = text.replace(tag, "").strip()
            return text
    return ""


def looks_like_web_spam(text: str) -> bool:
    """Detect pasted search/wiki marketing text that must never be shown as chat."""
    s = (text or "").strip()
    if not s:
        return False
    low = s.lower()
    spam_bits = (
        "enjoy the videos and music you love",
        "upload original content",
        "the correct form is",
        "the preferred form",
        "preferred form",
        "country code top-level domain",
        "live knowledge (retrieved",
        "om-1.0 should treat the facts",
        "youtube.com",
        "en.wikipedia.org",
        "upgrade upgrade",
        "membership of",
        "harry potter",
        "knockoff",
        "overpriced",
        "documentary presence",
        "released label",
        "on dvd",
        "sale by",
        "http://",
        "https://",
        "www.",
        "email@",
        "href=",
    )
    if any(b in low for b in spam_bits):
        return True
    # Long multi-topic dumps with no clear assistant voice.
    if len(s) > 180 and s.count(".") >= 4 and (" and " in low) and ("the " in low):
        markers = ("hi!", "hello", "i'm om", "i am om", "how can i help")
        if not any(m in low for m in markers):
            return True
    return False


@dataclass(frozen=True)
class ChatBackendInfo:
    backend: BackendName
    model: str
    detail: str = ""
    provider: str = ""
    live_knowledge: dict[str, Any] | None = None


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _env_on(name: str, default: str = "1") -> bool:
    return _env(name, default).lower() not in {"0", "false", "no", "off"}


def _env_float(name: str, default: float) -> float:
    raw = _env(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def openai_base_url() -> str:
    return _env("OM_AI_OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")


def openai_model() -> str:
    return _env("OM_AI_OPENAI_MODEL", "gpt-4o-mini")


def openai_api_key() -> str:
    return _env("OM_AI_OPENAI_API_KEY") or _env("OPENAI_API_KEY")


def configured_backend() -> str:
    """Resolve configured chat backend.

    Default when unset is ``om_native``. ``ollama`` is rejected in production —
    use ``om_ai.legacy.ollama`` only via explicit external scripts.
    """
    provider = (_env("OM_MODEL_PROVIDER") or "").lower()
    chat = (_env("OM_AI_CHAT_BACKEND") or _DEFAULT_BACKEND).lower()

    # An explicitly selected chat backend must win over a stale provider value.
    # This matters when an existing .env contains OM_MODEL_PROVIDER=om_native
    # but the operator intentionally switches chat to an OpenAI-compatible cloud.
    if chat in {"openai", "local"}:
        return chat
    if chat in {"om_native", "om-native", "native"}:
        return "om_native"
    if chat == "ollama" or provider == "ollama":
        raise RuntimeError(
            "Ollama is not part of the production chat path. "
            "Use an explicit supported backend (om_native, openai, or local). "
            "Legacy client (opt-in scripts only): om_ai.legacy.ollama"
        )
    if provider in {"om_native", "om-native", "native", "om"}:
        return "om_native"
    if provider in {"openai", "local"} and chat in {_DEFAULT_BACKEND, "auto"}:
        return provider
    if chat == "auto":
        if openai_configured():
            return "openai"
        return "local"
    if not chat:
        return _DEFAULT_BACKEND
    return chat


def openai_configured() -> bool:
    return bool(openai_api_key())


def resolve_backend(*, local_loaded: bool = False, native_ready: bool = False) -> ChatBackendInfo:
    """Pick the active chat backend for this process."""
    mode = configured_backend()
    if mode == "om_native":
        return ChatBackendInfo(
            "om_native",
            _env("OM_MODEL_ID", "OM-1.0") or "OM-1.0",
            "OM_MODEL_PROVIDER/OM_AI_CHAT_BACKEND=om_native (default)"
            + (" (ready)" if native_ready else " (checkpoint required)"),
            provider="OM AI",
        )
    if mode in {"openai", "local"}:
        if mode == "openai":
            return ChatBackendInfo(
                "openai",
                openai_model(),
                "forced by OM_AI_CHAT_BACKEND=openai",
                provider="OpenAI",
            )
        return ChatBackendInfo(
            "local",
            _env("OM_AI_MODEL_ID", "om-tiny") or "om-tiny",
            "forced by OM_AI_CHAT_BACKEND=local",
            provider="OM AI",
        )

    # auto — never picks Ollama
    if openai_configured():
        return ChatBackendInfo(
            "openai", openai_model(), "auto: OpenAI API key present", provider="OpenAI"
        )
    return ChatBackendInfo(
        "local",
        _env("OM_AI_MODEL_ID", "om-tiny") or "om-tiny",
        "auto: local OM" + (" (loaded)" if local_loaded else " (may be unloaded)"),
        provider="OM AI",
    )


def _normalize_messages(messages: list[dict]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for m in messages:
        role = str(m.get("role") or "user")
        content = m.get("content")
        if content is None:
            content = ""
        elif not isinstance(content, str):
            content = str(content)
        out.append({"role": role, "content": content})
    return out


def om_system_identity_text() -> str:
    return OM_SYSTEM_IDENTITY


def runtime_date_system_text(*, today: date | None = None) -> str:
    """Build a dynamic date/year system prompt from the real calendar date."""
    d = today or date.today()
    human = d.strftime(f"%A, %B {d.day}, %Y")
    tz_name = _env("OM_TIMEZONE") or _env("TZ") or "UTC"
    try:
        ZoneInfo(tz_name)
    except Exception:
        tz_name = "UTC"
    return (
        f"{OM_SYSTEM_IDENTITY} "
        f"Today's date is {human}. "
        f"Always treat the current year as {d.year}. "
        f"Timezone: {tz_name}."
    )


def runtime_date_system_text_compact(*, today: date | None = None) -> str:
    """Ultra-short system line for tiny context windows (e.g. max_seq_len=128)."""
    d = today or date.today()
    return f"You are OM AI. Today is {d.isoformat()} ({d.year})."


def with_runtime_date_context(
    messages: list[dict],
    *,
    today: date | None = None,
) -> list[dict[str, str]]:
    """Ensure messages include OM identity + accurate runtime date context."""
    date_line = runtime_date_system_text(today=today)
    msgs = _normalize_messages(messages)
    for i, m in enumerate(msgs):
        if m["role"] != "system":
            continue
        content = (m["content"] or "").strip()
        if "Today's date is " in content and "Always treat the current year as " in content:
            if "OM-1.0 native language model" not in content:
                msgs[i] = {"role": "system", "content": f"{OM_SYSTEM_IDENTITY}\n\n{content}"}
            return msgs
        if "Today's date is " in content and "The current year is " in content:
            if "OM-1.0 native language model" not in content:
                msgs[i] = {"role": "system", "content": f"{OM_SYSTEM_IDENTITY}\n\n{content}"}
            return msgs
        merged = f"{content}\n\n{date_line}" if content else date_line
        msgs[i] = {"role": "system", "content": merged}
        return msgs
    return [{"role": "system", "content": date_line}] + msgs


def chat_via_openai(
    messages: list[dict],
    *,
    max_new_tokens: int = 256,
    temperature: float = 0.8,
    top_p: float = 1.0,
    model: str | None = None,
) -> str:
    key = openai_api_key()
    if not key:
        raise RuntimeError("OpenAI API key not set (OM_AI_OPENAI_API_KEY or OPENAI_API_KEY)")
    payload = {
        "model": model or openai_model(),
        "messages": _normalize_messages(messages),
        "max_tokens": int(max_new_tokens),
        "temperature": float(temperature),
        "top_p": float(top_p),
    }
    url = f"{openai_base_url()}/chat/completions"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=120.0) as client:
        r = client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
    try:
        return str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"OpenAI-compatible API returned unexpected payload: {data!r}") from exc



def _om_native_chat_reply_body(
    *,
    info: ChatBackendInfo,
    messages: list[dict],
    intel: Any,
    kwargs: dict[str, Any],
    native_chat: Callable[..., str] | None,
    language_context: dict[str, Any] | None = None,
    native_ready: bool,
    tenant_id: str | None,
    actor: str | None,
    project_id: str | None,
    project_instructions: str | None,
    force_tools: list[str] | None = None,
    evolution_level: float | None = None,
    evolution_profile: dict[str, Any] | None = None,
) -> tuple[str, ChatBackendInfo]:
    """Native chat cascade: understand/research/reason/generate — no static outlines."""
    from om_ai.runtime.engine import EMPTY_GENERATION_FALLBACK, usable_generation_text
    from om_ai.live_knowledge.freshness import is_greeting_like, is_om_self_query

    user_text = _latest_user_text(messages)
    if language_context is None:
        language_context = {}
    profile = dict(evolution_profile or {})

    # Slightly warmer greetings so replies vary (still model-generated).
    if is_greeting_like(user_text) or is_om_self_query(user_text):
        kwargs["temperature"] = max(float(kwargs["temperature"]), 0.5)
        kwargs["top_p"] = max(float(kwargs["top_p"]), 0.9)
        kwargs["top_k"] = max(int(kwargs["top_k"]), 40)
        kwargs["max_new_tokens"] = min(max(int(kwargs["max_new_tokens"]), 64), 96)
        kwargs["min_new_tokens"] = 1
        kwargs["repetition_penalty"] = max(float(kwargs["repetition_penalty"]), 1.08)

    info_base = ChatBackendInfo(
        backend=info.backend,
        model=info.model,
        detail=info.detail,
        provider=info.provider,
        live_knowledge={"intelligence": intel.meta} if intel.meta else None,
    )
    if intel.direct_reply:
        return intel.direct_reply, info_base

    # ── STEP 30 ChatGPT-like Brain Controller (preferred front door) ─
    if _env_on("OM_CHATGPT_RUNTIME", "1"):
        try:
            from om_ai.core.chatgpt_runtime import run_chatgpt_runtime

            hist = []
            for m in messages or []:
                if isinstance(m, dict) and m.get("content"):
                    hist.append(
                        {
                            "role": str(m.get("role") or "user"),
                            "content": str(m.get("content") or "")[:2000],
                        }
                    )

            def _model_gen(prompt: str, context: str = "") -> str:
                if not native_ready or not callable(native_chat):
                    return ""
                try:
                    from om_ai.runtime.chat_orchestrator import build_chat_messages

                    msgs = build_chat_messages(
                        prompt,
                        system=(context or "You are OM AI. Reply helpfully.")[:2000],
                        history=hist,
                    )
                    return str(native_chat(msgs, **(kwargs or {})) or "")
                except Exception:
                    try:
                        return str(native_chat(prompt) or "")
                    except Exception:
                        return ""

            crt = run_chatgpt_runtime(
                user_text,
                history=hist,
                tenant_id=tenant_id or "default",
                actor=actor or "",
                model_generate=_model_gen if native_ready else None,
                extra={
                    "project_id": project_id,
                    "project_instructions": project_instructions or "",
                },
            )
            ans = str(crt.get("answer") or "").strip()
            try:
                from om_ai.core.chat_intelligence.stub_detect import is_solution_stub
                from om_ai.core.intelligence.real_answer import looks_like_static_reply

                if is_solution_stub(ans) or looks_like_static_reply(ans):
                    ans = ""
            except Exception:
                pass
            if ans and not ResponseEcho.check(user_text, ans):
                info_crt = ChatBackendInfo(
                    backend=info.backend,
                    model=info.model,
                    detail="chatgpt_runtime_step30",
                    provider=info.provider,
                    live_knowledge={
                        "intelligence": intel.meta,
                        "chatgpt_runtime": crt.get("meta") or {},
                        "stages": crt.get("stages") or [],
                        "source": crt.get("source"),
                        "evolution_level": evolution_level,
                    },
                )
                return ans if ans.endswith("\n") else ans + "\n", info_crt
        except Exception as exc:
            logger.debug("chatgpt_runtime skipped: %s", exc)

    # ── Upgraded chat pipeline ───────────────────────────────────────
    # Language → Intent → Reasoning → Model → Language Check → Final
    if _env_on("OM_CHAT_PIPELINE", "1"):
        try:
            from om_ai.runtime.chat_pipeline import run_chat_pipeline

            piped = run_chat_pipeline(
                user_text,
                messages=messages,
                native_chat=native_chat,
                native_ready=native_ready,
                kwargs=kwargs,
                tenant_id=tenant_id or "default",
                actor=actor or "",
                project_id=project_id,
                project_instructions=project_instructions or "",
                force_tools=force_tools,
                evolution_level=evolution_level,
                evolution_profile=profile,
            )
            ans = str(piped.get("answer") or "").strip()
            if ans and not ResponseEcho.check(user_text, ans):
                info_pipe = ChatBackendInfo(
                    backend=info.backend,
                    model=info.model,
                    detail="chat_pipeline_v2",
                    provider=info.provider,
                    live_knowledge={
                        "intelligence": intel.meta,
                        "pipeline": piped.get("meta") or {},
                        "stages": piped.get("stages") or [],
                        "language": (piped.get("language") or {}).get("response_language"),
                        "intent": (piped.get("intent") or {}).get("intent"),
                        "evolution_level": evolution_level,
                        "evolution_model": (profile or {}).get("model_id"),
                    },
                )
                return ans if ans.endswith("\n") else ans + "\n", info_pipe
        except Exception as exc:
            logger.debug("chat_pipeline_v2 skipped: %s", exc)

    # Universal multimodal + cognitive loop (preferred).
    if _env_on("OM_UNIVERSAL_INTELLIGENCE", "1"):
      try:
        from om_ai.operating_intelligence.universal import UniversalIntelligence
        from om_ai.core.response.response_formatter import (
            ensure_public_reply,
            looks_like_pipeline_dump,
            response_mode,
        )
        from om_ai.response_engine import format_assistant_reply

        uni = UniversalIntelligence().run(
            user_text,
            messages=messages,
            project=project_id,
        )
        uni_ans = str(uni.get("answer") or "").strip()
        if uni.get("deferred") or not uni_ans:
            raise RuntimeError("universal deferred")
        try:
            from om_ai.core.intelligence.real_answer import looks_like_static_reply

            if looks_like_static_reply(uni_ans):
                raise RuntimeError("universal static rejected")
        except ImportError:
            pass
        if uni_ans and not looks_like_pipeline_dump(uni_ans) and not ResponseEcho.check(user_text, uni_ans):
            polished = format_assistant_reply(
                uni_ans,
                intent=str(uni.get("intent") or "chat"),
                enhance=True,
            )
    # Universal / cognitive early returns — never polish to blank
            if response_mode() != "developer":
                polished = ensure_public_reply(user_text, polished, {
                    "intent": {"intent": uni.get("intent")},
                    "intelligence": uni.get("cognitive") or {},
                })
            if not (polished or "").strip():
                raise RuntimeError("universal polished empty")
            try:
                from om_ai.core.intelligence.real_answer import looks_like_static_reply

                # Only reject outline dumps — allow greetings
                if looks_like_static_reply(polished) and len(polished) > 160:
                    raise RuntimeError("universal polished static")
            except ImportError:
                pass
            if not ResponseEcho.check(user_text, polished) and len(polished.strip()) >= 8:
                info_uni = ChatBackendInfo(
                    backend=info.backend,
                    model=info.model,
                    detail="universal_intelligence",
                    provider=info.provider,
                    live_knowledge={
                        "intelligence": intel.meta,
                        "universal": {
                            "intent": uni.get("intent"),
                            "capability": uni.get("capability"),
                            "stages": uni.get("stages"),
                            "modality": (uni.get("multimodal") or {}).get("modality"),
                        },
                    },
                )
                return polished, info_uni
      except Exception as exc:
        logger.debug("UniversalIntelligence skipped: %s", exc)

    # Core cognitive intelligence (understand → capability → verify).
    if _env_on("OM_COGNITIVE_INTELLIGENCE", "1"):
      try:
        from om_ai.core.intelligence import CognitiveIntelligence
        from om_ai.core.response.response_formatter import (
            ensure_public_reply,
            looks_like_pipeline_dump,
            response_mode,
        )
        from om_ai.response_engine import format_assistant_reply

        cog_intel = CognitiveIntelligence().run(
            user_text,
            messages=messages,
            project=project_id,
        )
        cog_ans = str(cog_intel.get("answer") or "").strip()
        val = cog_intel.get("validation") or {}
        # Skip deferred / empty / static outlines — continue to Absolute OS / model
        if cog_intel.get("deferred") or not cog_ans:
            raise RuntimeError("cognitive capability deferred")
        try:
            from om_ai.core.intelligence.real_answer import looks_like_static_reply

            if looks_like_static_reply(cog_ans):
                raise RuntimeError("static capability outline rejected")
        except ImportError:
            pass
        if (
            cog_ans
            and not looks_like_pipeline_dump(cog_ans)
            and float(val.get("score") or 0) >= 75
            and not ResponseEcho.check(user_text, cog_ans)
        ):
            polished = format_assistant_reply(
                cog_ans,
                intent=str((cog_intel.get("intent") or {}).get("intent") or "chat"),
                enhance=True,
            )
            if response_mode() != "developer":
                polished = ensure_public_reply(user_text, polished, {
                    "intent": cog_intel.get("intent") or {},
                    "intelligence": cog_intel,
                })
            # Final echo guard
            if not ResponseEcho.check(user_text, polished):
                info_ci = ChatBackendInfo(
                    backend=info.backend,
                    model=info.model,
                    detail="cognitive_intelligence",
                    provider=info.provider,
                    live_knowledge={
                        "intelligence": intel.meta,
                        "cognitive": {
                            "intent": (cog_intel.get("understanding") or {}).get("intent"),
                            "capability": (cog_intel.get("capability") or {}).get("id"),
                            "score": val.get("score"),
                        },
                    },
                )
                return polished, info_ci
      except Exception as exc:
        logger.debug("CognitiveIntelligence skipped: %s", exc)

    # Dynamic intelligence pipeline (generalizes; regex only as helper signals).
    if _env_on("OM_DYNAMIC_INTELLIGENCE", "1"):
      try:
        from om_ai.intelligence import IntelligenceManager
        from om_ai.core.response.response_formatter import (
            ensure_public_reply,
            looks_like_pipeline_dump,
            response_mode,
        )
        from om_ai.response_engine import format_assistant_reply

        dyn = IntelligenceManager().run(
            user_text,
            messages=messages,
            project=project_id,
        )
        dyn_answer = str(dyn.get("answer") or "").strip()
        if not dyn_answer:
            raise RuntimeError("dynamic empty")
        try:
            from om_ai.core.intelligence.real_answer import looks_like_static_reply

            if looks_like_static_reply(dyn_answer):
                raise RuntimeError("dynamic static rejected")
        except ImportError:
            pass
        if dyn_answer and not looks_like_pipeline_dump(dyn_answer) and not ResponseEcho.check(user_text, dyn_answer):
            eval_ok = float((dyn.get("evaluation") or {}).get("score") or 0) >= 75
            intent_name = str((dyn.get("intent") or {}).get("intent") or "")
            # Date / calc / create_prompt can be short; everything else needs real length + score
            allow_short = intent_name in {"datetime", "calculate", "chat", "create_prompt"}
            if (eval_ok or allow_short) and (len(dyn_answer) >= 40 or allow_short):
                polished = format_assistant_reply(
                    dyn_answer,
                    intent=intent_name or "chat",
                    enhance=True,
                )
                if response_mode() != "developer":
                    polished = ensure_public_reply(user_text, polished, {
                        "intent": dyn.get("intent") or {},
                        "intelligence": dyn,
                    })
                try:
                    from om_ai.core.intelligence.real_answer import looks_like_static_reply

                    if looks_like_static_reply(polished):
                        raise RuntimeError("dynamic polished static")
                except ImportError:
                    pass
                info_dyn = ChatBackendInfo(
                    backend=info.backend,
                    model=info.model,
                    detail="dynamic_intelligence",
                    provider=info.provider,
                    live_knowledge={
                        "intelligence": intel.meta,
                        "dynamic": {
                            "intent": intent_name,
                            "agents": (dyn.get("agents") or {}).get("team"),
                            "tools": (dyn.get("tools") or {}).get("tools"),
                            "score": (dyn.get("evaluation") or {}).get("score"),
                        },
                    },
                )
                return polished, info_dyn
      except Exception as exc:
        logger.debug("IntelligenceManager skipped: %s", exc)

    # Structured cognitive brain — instance.process(question), never import-time.
    from om_ai.runtime.chat_orchestrator import run_cognitive_brain
    from om_ai.response_engine import format_assistant_reply
    from om_ai.understanding.query_kind import is_greeting, query_kind

    skip_cog = is_greeting(user_text)
    try:
        if not skip_cog:
            cog = run_cognitive_brain(user_text, native_chat=native_chat)
            from om_ai.core.response.response_formatter import (
                ensure_public_reply,
                looks_like_pipeline_dump,
                response_mode,
            )

            cog_answer = str(
                cog.get("user_response") or cog.get("answer") or ""
            ).strip()
            if response_mode() == "developer":
                cog_answer = str(cog.get("developer_response") or cog_answer).strip()
            else:
                cog_answer = ensure_public_reply(user_text, cog_answer, {
                    "intent": cog.get("intent") or {},
                    "technology": cog.get("technology") or {},
                    "plan": (cog.get("tasks") or {}).get("tasks") or [],
                    "architecture": (cog.get("reasoning") or {}).get("architecture") or [],
                    "evaluation": cog.get("evaluation") or {},
                })
            if (
                cog_answer
                and len(cog_answer) > 20
                and (response_mode() == "developer" or not looks_like_pipeline_dump(cog_answer))
            ):
                polished = format_assistant_reply(
                    cog_answer,
                    intent=query_kind(user_text),
                    enhance=True,
                )
                if response_mode() != "developer":
                    polished = ensure_public_reply(user_text, polished)
                info_cog = ChatBackendInfo(
                    backend=info.backend,
                    model=info.model,
                    detail=info.detail,
                    provider=info.provider,
                    live_knowledge={"intelligence": intel.meta} if intel.meta else None,
                )
                return polished, info_cog
    except Exception as exc:
        logger.debug("OMCognitiveBrain.process skipped: %s", exc)

    # Absolute Intelligence OS — full cognitive cycle (memory/knowledge/reason/agents/learn)
    absolute_on = (_env("OM_ABSOLUTE_OS") or "1").lower() not in {"0", "false", "no", "off"}
    if absolute_on and user_text.strip() and not (
        is_greeting_like(user_text) and len(user_text.split()) <= 4
    ):
        try:
            from om_ai.operating_intelligence import OperatingIntelligence

            cycle = OperatingIntelligence().run(
                user_text,
                context={
                    "tenant_id": tenant_id or "default",
                    "actor": actor or "",
                    "project_id": project_id,
                    "messages": messages,
                    "project_instructions": project_instructions or "",
                },
                dry_run=True,
            )
            abs_reply = (cycle.response or "").strip()
            if abs_reply and len(abs_reply) > 40:
                info_abs = ChatBackendInfo(
                    backend=info.backend,
                    model=info.model,
                    detail=info.detail,
                    provider=info.provider,
                    live_knowledge={
                        "intelligence": intel.meta,
                        "absolute_os": {
                            "intent": (cycle.understood or {}).get("intent"),
                            "agents": (cycle.agents or {}).get("agents"),
                            "knowledge_source": (cycle.knowledge or {}).get("source"),
                            "verification": cycle.verification,
                            "growth_ok": bool((cycle.growth or {}).get("ok", True)),
                        },
                    },
                )
                # Still polish via response intelligence
                from om_ai.response_engine import format_assistant_reply
                from om_ai.core.response.intelligence import ensure_intelligent_response

                try:
                    repaired = ensure_intelligent_response(
                        user_text,
                        abs_reply,
                        intent=str((cycle.understood or {}).get("intent") or "chat"),
                    )
                    polished = format_assistant_reply(
                        repaired.get("final") or abs_reply,
                        intent=str((cycle.understood or {}).get("intent") or "chat"),
                        enhance=True,
                    )
                except Exception:
                    polished = abs_reply
                from om_ai.core.response.response_formatter import ensure_public_reply, response_mode

                if response_mode() != "developer":
                    polished = ensure_public_reply(user_text, polished)
                return polished, info_abs
        except Exception as exc:
            logger.debug("absolute OS cycle skipped: %s", exc)

    # Agent Brain v1: intent → memory/RAG/plan hints (self-owned, no external LLM).
    from om_ai.agent import AgentBrain

    brain_decision = AgentBrain().prepare(
        messages,
        tenant_id=tenant_id or "default",
        actor=actor or "",
        project_id=project_id,
        project_instructions=project_instructions or "",
    )
    messages = brain_decision.packed_messages or messages

    # Prefer a single short system for tiny OM-1.0 windows.
    # Do NOT stack extra system lines — that breaks chat-SFT greets.
    if is_greeting_like(user_text) or is_om_self_query(user_text):
        extra = None
    else:
        extra = runtime_date_system_text_compact()
        if intel.extra_system:
            hint = intel.extra_system.strip()
            if len(hint) > 120:
                hint = hint[:117] + "..."
            extra = f"{extra}\n{hint}" if extra else hint
        if brain_decision.extra_system:
            bh = brain_decision.extra_system.strip()
            if len(bh) > 160:
                bh = bh[:157] + "..."
            extra = f"{extra}\n{bh}" if extra else bh

    # Chat template: system + turns. Compact for tiny local windows.
    messages = build_chat_messages(
        messages,
        compact=True,
        extra_system=extra,
    )
    # Skip live web for greetings / OM-self so chat never becomes paste spam.
    skip_live = is_greeting_like(user_text) or is_om_self_query(user_text)

    lk_meta: dict[str, Any] = {}
    if not skip_live:
        try:
            from om_ai.live_knowledge import enrich_messages_for_live_knowledge

            messages, lk_meta = enrich_messages_for_live_knowledge(messages)
        except Exception as exc:
            logger.debug("live_knowledge enrich skipped: %s", exc)

    grounded = (lk_meta.get("grounded_reply") or "").strip()
    if grounded:
        from om_ai.live_knowledge.engine import strip_live_knowledge_boilerplate

        grounded = strip_live_knowledge_boilerplate(grounded)
        if looks_like_web_spam(grounded):
            grounded = ""
    dataset_grounded = ""
    if brain_decision.prefer_grounded:
        dataset_grounded = brain_decision.prefer_grounded.strip()
    if not grounded and dataset_grounded:
        grounded = dataset_grounded
    prefer_grounded = bool(lk_meta.get("prefer_grounded_reply")) and bool(grounded)
    grounded_env = (_env("OM_LIVE_KNOWLEDGE_GROUNDED") or "0").lower()
    live_grounded_allowed = (
        grounded_env not in {"0", "false", "no", "off"} and not skip_live
    )
    # Dataset / RAG grounded answers are always allowed (local corpora, not web).
    grounded_allowed = live_grounded_allowed or bool(dataset_grounded)
    merged_lk = {
        **({k: v for k, v in lk_meta.items() if k != "grounded_reply"} or {}),
        "intelligence": intel.meta,
    }
    info_lk = ChatBackendInfo(
        backend=info.backend,
        model=info.model,
        detail=info.detail,
        provider=info.provider,
        live_knowledge=merged_lk or None,
    )
    intent_v = brain_decision.intent.value

    def _out(text: str) -> tuple[str, ChatBackendInfo]:
        from om_ai.response_engine import format_assistant_reply
        from om_ai.core.response.intelligence import ensure_intelligent_response
        from om_ai.core.response.response_formatter import ensure_public_reply, response_mode

        try:
            repaired = ensure_intelligent_response(
                user_text,
                text or "",
                intent=intent_v,
            )
            polished = format_assistant_reply(
                repaired.get("final") or text or "",
                intent=intent_v,
                enhance=True,
            )
        except Exception:
            polished = (text or "").strip()
        if response_mode() != "developer":
            polished = ensure_public_reply(user_text, polished, {
                "intent": {"intent": intent_v},
            })
        # Never show a blank bubble in the UI
        if not (polished or "").strip():
            try:
                from om_ai.agent.verifier import compose_fallback

                polished = compose_fallback(intent=intent_v, user_text=user_text)
            except Exception:
                polished = "Hello — I’m OM. How can I help you?"
            return (polished or "").strip() + "\n", info_lk
        # OM Response Language Check
        if _language_manager:
            try:
                response_lang = (
                    language_context
                    .get("response_language")
                )
                if response_lang:
                    logger.info(
                        "Response language: %s",
                        response_lang
                    )
            
            except Exception:
                pass

    # Prefer local dataset/RAG grounded reply before tiny-model garble.
    if dataset_grounded and len(dataset_grounded) > 80:
        return _out(dataset_grounded)

    if prefer_grounded and live_grounded_allowed and grounded:
        return _out(grounded)

    if native_chat is None or not native_ready:
        from om_ai.core.response.response_formatter import ensure_public_reply

        public = ensure_public_reply(user_text, "")
        if public.strip():
            return _out(public)
        raise NativeCheckpointError("OM-1.0 checkpoint unavailable.")

    try:
        text = native_chat(messages, **kwargs)
    except NativeCheckpointError:
        raise
    except Exception as exc:
        raise NativeCheckpointError(
            f"OM-1.0 checkpoint unavailable. ({exc})"
        ) from exc

    # Model-first: accept usable generation; reject garbled tiny-model soup.
    fail = is_low_quality_reply(text)
    # Tiny models often start with "Hello" then derail — use Agent Brain fallback.
    if (
        not fail
        and brain_decision.intent.value in {"greeting", "identity"}
        and brain_decision.structured_fallback
    ):
        from om_ai.runtime.chat_orchestrator import (
            is_nonsensical_smalltalk,
            looks_like_assistant_chitchat,
        )

        probe = (usable_generation_text(text) or text or "").strip()
        if is_nonsensical_smalltalk(probe) or not looks_like_assistant_chitchat(probe):
            return _out(brain_decision.structured_fallback)

    # Coding / planning: prefer structured reasoning if model is weak/garbled.
    if fail and brain_decision.intent.value in {"coding", "agent", "knowledge"}:
        rescued_early = brain_decision.after_model(text) or brain_decision.structured_fallback
        if rescued_early:
            return _out(rescued_early)

    if not fail:
        cleaned = usable_generation_text(text) or ""
        cleaned = cleaned.lstrip(" ,.;:\"'`-—–")
        if cleaned and looks_like_web_spam(cleaned):
            first = re.split(r"(?<=[.!?।])\s+", cleaned, maxsplit=1)[0].strip()
            if first and not looks_like_web_spam(first) and len(first) <= 160:
                cleaned = first
        # Memorized script line → warmer model re-samples (still not static text).
        if cleaned and _looks_scripted(cleaned):
            best = cleaned
            try:
                for attempt in range(3):
                    alt_kwargs = dict(kwargs)
                    alt_kwargs.update(
                        {
                            "temperature": 0.7 + 0.1 * attempt,
                            "top_p": 0.92,
                            "top_k": 60,
                            "max_new_tokens": max(int(kwargs["max_new_tokens"]), 80),
                            "repetition_penalty": max(
                                float(kwargs["repetition_penalty"]), 1.18
                            ),
                        }
                    )
                    alt = native_chat(messages, **alt_kwargs)
                    alt_fail = is_low_quality_reply(alt)
                    if alt_fail:
                        continue
                    alt_clean = (usable_generation_text(alt) or "").lstrip(
                        " ,.;:\"'`-—–"
                    )
                    if not alt_clean or looks_like_web_spam(alt_clean):
                        continue
                    if not _looks_scripted(alt_clean):
                        return _out(alt_clean)
                    best = alt_clean
            except Exception as exc:
                logger.debug("script diversify skipped: %s", exc)
            # Prefer any model variant over injecting canned copy.
            return _out(best)
        if cleaned and not looks_like_web_spam(cleaned):
            return _out(cleaned)
        fail = "spam"

    if grounded_allowed and grounded and not looks_like_web_spam(grounded):
        return _out(grounded)

    # Safer OM-1.0 retry with stronger anti-repetition (still model output only).
    try:
        retry_kwargs = dict(kwargs)
        retry_kwargs.update(
            {
                "max_new_tokens": max(int(kwargs["max_new_tokens"]), 96),
                "temperature": 0.4,
                "top_p": 0.9,
                "top_k": 40,
                "repetition_penalty": max(float(kwargs["repetition_penalty"]), 1.12),
                "min_new_tokens": 1,
            }
        )
        retry = native_chat(messages, **retry_kwargs)
        retry_fail = is_low_quality_reply(retry)
        if not retry_fail:
            retry = (usable_generation_text(retry) or "").lstrip(" ,.;:\"'`-—–")
            if retry and not looks_like_web_spam(retry):
                return _out(retry)
            retry_fail = "spam"
        if retry_fail:
            fail = retry_fail
    except Exception as exc:
        logger.debug("native retry skipped: %s", exc)

    # Agent Brain structured fallback (coding/agent/knowledge) before empty hint.
    rescued = brain_decision.after_model(None)
    if not rescued and brain_decision.structured_fallback:
        rescued = brain_decision.structured_fallback
    if rescued:
        return _out(rescued)

    # Last resort — never return blank / "(empty reply)"
    try:
        from om_ai.agent.verifier import compose_fallback

        fb = compose_fallback(intent=intent_v, user_text=user_text)
        if fb and fb.strip():
            return _out(fb)
    except Exception:
        pass
    return _out("Hello — I’m OM. How can I help you?")

def chat_reply(
    messages: list[dict],
    *,
    local_chat: Callable[..., str] | None = None,
    local_loaded: bool = False,
    native_chat: Callable[..., str] | None = None,
    native_ready: bool = False,
    max_new_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    top_k: int | None = None,
    repetition_penalty: float | None = None,
    tenant_id: str = "default",
    actor: str = "",
    assistant_instructions: str = "",
    project_instructions: str = "",
    project_id: str | None = None,
    model: str | None = None,
    force_tools: list[str] | None = None,
) -> tuple[str, ChatBackendInfo]:
    """Generate a chat reply and return ``(text, backend_info)``.

    Pipeline: Language → Memory → Intent → Reasoning → Model → Language Check → Final
    """
    from om_ai.runtime.chat_orchestrator import (
        build_chat_messages,
        generation_config,
        is_low_quality_reply,
    )
    from om_ai.runtime.evolution_matrix import (
        level_runtime_profile,
        maybe_evolution_reply,
    )
    from om_ai.runtime.intelligence import enrich_for_chat

    # Sanitize legacy UI tool tags from user turns.
    cleaned_messages = []
    for m in messages or []:
        role = str(m.get("role") or "user")
        content = str(m.get("content") or "")
        if role == "user":
            for tag in ("[web search enabled]", "[code interpreter enabled]"):
                content = content.replace(tag, "")
            content = content.strip()
        cleaned_messages.append({"role": role, "content": content})
    messages = cleaned_messages

    profile = level_runtime_profile(model)
    evo_text, evo_model, evo_level = maybe_evolution_reply(messages, model=model)
    if evo_text is not None:
        info = ChatBackendInfo(
            backend="om_evolution",
            model=evo_model,
            provider="OM AI Matrix",
        )
        return evo_text, info
    # Remember selected evolution model id for branding when we fall through to native.
    selected_evolution_model = evo_model if evo_level is not None else None

    def _brand(info: ChatBackendInfo) -> ChatBackendInfo:
        if not selected_evolution_model or info.model == selected_evolution_model:
            return info
        return ChatBackendInfo(
            backend=info.backend,
            model=selected_evolution_model,
            detail=info.detail,
            provider=info.provider or "OM AI",
            live_knowledge=info.live_knowledge,
        )

    # Language intelligence (optional, never blocks chat)
    language_context: dict[str, Any] = {}
    if _language_manager is not None:
        try:
            language_context = _language_manager.process(_latest_user_text(messages)) or {}
            logger.info("OM Language detected: %s", language_context.get("language"))
        except Exception as exc:
            logger.debug("Language intelligence skipped: %s", exc)
            language_context = {}

    info = resolve_backend(local_loaded=local_loaded, native_ready=native_ready)
    if info.backend == "om_native":
        env_temp = _env_float("OM_CHAT_TEMPERATURE", 0.7)
        env_max = _env_int("OM_CHAT_MAX_NEW_TOKENS", 96)
        # Apply selected OM level temperature / token budget.
        level_temp = float(profile.get("temperature") or env_temp)
        level_max = int(profile.get("max_tokens") or env_max)
        if temperature is None or float(temperature) > 0.85:
            temperature = level_temp if evo_level is not None else env_temp
        if max_new_tokens is None or int(max_new_tokens) > env_max:
            max_new_tokens = min(level_max, env_max) if evo_level is not None else env_max
            # Higher levels get a bit more room within the server cap.
            if evo_level is not None and evo_level >= 4.0:
                max_new_tokens = min(max(int(max_new_tokens), 128), max(env_max, 192))
    gen = generation_config(
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        repetition_penalty=repetition_penalty,
    )
    kwargs: dict[str, Any] = {
        "max_new_tokens": int(gen["max_new_tokens"]),
        "temperature": float(gen["temperature"]),
        "top_p": float(gen["top_p"]),
        "top_k": int(gen["top_k"]),
        "repetition_penalty": float(gen["repetition_penalty"]),
        "min_new_tokens": int(gen["min_new_tokens"]),
        "no_repeat_ngram_size": int(gen.get("no_repeat_ngram_size", 3)),
        "repetition_window": int(gen.get("repetition_window", 128)),
    }

    if not assistant_instructions:
        for m in messages or []:
            if str(m.get("role") or "") == "system":
                content = str(m.get("content") or "").strip()
                if content and "Today's date" not in content:
                    assistant_instructions = content
                    break

    # Inject active OM level so native path follows the user's picker.
    hint = str(profile.get("system_hint") or "").strip()
    if hint and evo_level is not None:
        messages = list(messages) + [
            {
                "role": "system",
                "content": hint,
            }
        ]

    intel = enrich_for_chat(
        messages,
        tenant_id=tenant_id or "default",
        actor=actor or "",
        assistant_instructions=assistant_instructions or "",
        project_instructions=project_instructions or "",
        project_id=project_id,
        compact=True,
    )

    if language_context.get("response_language") or language_context.get("language"):
        lang = language_context.get("response_language") or language_context.get("language")
        instruction = language_context.get("instruction") or (
            f"Reply in the same language as the user ({lang})."
        )
        messages = list(messages) + [
            {
                "role": "system",
                "content": f"Language context:\nUser language: {lang}\n{instruction}",
            }
        ]

    if info.backend == "om_native":
        os.environ["_OM_IN_CHAT_REPLY"] = "1"
        try:
            text, info = _om_native_chat_reply_body(
                info=info,
                messages=messages,
                intel=intel,
                kwargs=kwargs,
                language_context=language_context,
                native_chat=native_chat,
                native_ready=native_ready,
                tenant_id=tenant_id,
                actor=actor,
                project_id=project_id,
                project_instructions=project_instructions,
                force_tools=force_tools,
                evolution_level=evo_level,
                evolution_profile=profile,
            )
            return text, _brand(info)
        finally:
            os.environ.pop("_OM_IN_CHAT_REPLY", None)

    messages = with_runtime_date_context(messages)
    if info.backend == "openai":
        text = chat_via_openai(
            messages,
            model=info.model,
            max_new_tokens=int(kwargs["max_new_tokens"]),
            temperature=float(kwargs["temperature"]),
            top_p=float(kwargs["top_p"]),
        )
        return text, _brand(info)

    if local_chat is None or not local_loaded:
        raise RuntimeError(
            "No chat backend available. Set OM_MODEL_PROVIDER=om_native with a real "
            "OM-1.0 checkpoint, load a local OM checkpoint (OM_AI_AUTOLOAD=1), or set "
            "OM_AI_OPENAI_API_KEY / OPENAI_API_KEY with OM_AI_CHAT_BACKEND=openai."
        )
    return local_chat(messages, **kwargs), _brand(info)

def backend_status(*, local_loaded: bool = False, native_ready: bool = False) -> dict[str, Any]:
    info = resolve_backend(local_loaded=local_loaded, native_ready=native_ready)
    return {
        "backend": info.backend,
        "model": info.model,
        "provider": info.provider,
        "detail": info.detail,
        "configured": configured_backend(),
        "openai_configured": openai_configured(),
        "local_loaded": local_loaded,
        "native_ready": native_ready,
        "external_llm": "none" if info.backend == "om_native" else info.backend,
    }
