"""
OM Voice Presence Engine — dynamic spoken conversation layer.

Shapes brain text for speech. Never speaks internal chrome.
Recovery prefers live generation; last-resort lines are composed from signals
(not fixed FAQ scripts).
"""
from __future__ import annotations

import re
from typing import Any

from .conversation_presence import ConversationPresence
from .emotion_detector import EmotionDetector
from .language_engine import LanguageEngine
from .personality_rules import PersonalityRules
from .response_adapter import ResponseAdapter
from .speech_style import SpeechStyle

_ENGINE: VoicePresenceEngine | None = None

_INTERNAL_LEAK = re.compile(
    r"(?is)("
    r"agent\s*\[|agent\s*goal\s*\[|collaboration\s*:|"
    r"knowledge investigation required|retrieve context|"
    r"retrieve information|research:\s*knowledge|"
    r"\[layered\]|\[decision\]|\[workflow\]|"
    r"self-critique|pipeline trace|om-ai brain power|"
    r"heuristic foundation path|context_blob|"
    r"trace_id|internal_context|stage[s]?\s*:"
    r")"
)

_GARBAGE_MARKERS = (
    "rephrase",
    "one short sentence",
    "short sentence",
    "plain words",
    "as an ai",
    "i'm just a language model",
    "i want to help",
    "could you rephrase",
    "please rephrase",
    "didn't understand",
    "do not understand",
    "don't understand",
    "cannot understand",
    "say that again",
    "in your own words",
    "share a bit more detail",
    "share one more detail",
    "goal, error, or constraint",
    "i can help with that",
    "wasn't reliable",
    "ask again in one short",
    "how can i help you",
    "what can i do for you",
    "couldn't understand that message",
    "couldn’t understand that message",
    "please ask again",
    "plain-language explanation",
    "best understood by",
    "ask for a deeper dive",
    "knowledge investigation required",
    "retrieve context",
    "retrieve information",
)


class VoicePresenceEngine:
    def __init__(self) -> None:
        self.language = LanguageEngine()
        self.emotion = EmotionDetector()
        self.style = SpeechStyle()
        self.personality = PersonalityRules()
        self.adapter = ResponseAdapter()
        self.presence = ConversationPresence()

    def analyze(
        self,
        user_message: str,
        response: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = dict(context or {})
        locale = self.language.detect(user_message)
        emotion = self.emotion.detect(user_message)
        context.setdefault("locale", locale)
        context.setdefault("emotion", emotion)
        context.setdefault("user_message", user_message)
        personality = self.personality.profile(context)
        presence = self.presence.on_user(emotion)

        cleaned = strip_internal_chrome(response)
        adapted = self.adapter.adapt(
            cleaned,
            locale=locale,
            emotion=emotion,
            personality=personality,
        )
        spoken = adapted["spoken"]

        if is_garbage_spoken(spoken):
            spoken = soft_listening_fallback(
                locale=locale,
                user_message=user_message,
                emotion=emotion,
                context=context,
            )
            adapted = self.adapter.adapt(
                spoken,
                locale=locale,
                emotion=emotion,
                personality=personality,
            )

        self.presence.on_assistant(speaking=True)
        return {
            "spoken": adapted["spoken"],
            "spoken_tts": adapted["spoken_tts"],
            "display": adapted.get("display") or adapted["spoken"],
            "locale": locale,
            "emotion": emotion,
            "personality": personality,
            "presence": presence,
            "trimmed": adapted.get("trimmed", False),
        }

    def system_prompt(self, context: dict[str, Any] | None = None) -> str:
        context = dict(context or {})
        if "locale" not in context and context.get("user_message"):
            context["locale"] = self.language.detect(str(context["user_message"]))
        if "emotion" not in context and context.get("user_message"):
            context["emotion"] = self.emotion.detect(str(context["user_message"]))
        return self.personality.system_prompt(context)


def get_voice_presence() -> VoicePresenceEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = VoicePresenceEngine()
    return _ENGINE


def normalize_heard_text(text: str) -> str:
    return get_voice_presence().language.normalize_heard(text)


def detect_speech_locale(user_message: str) -> str:
    return get_voice_presence().language.detect(user_message)


def jarvis_system_hint(*, conversation_mode: str = "assist", locale: str = "en") -> str:
    return get_voice_presence().system_prompt(
        {"conversation_mode": conversation_mode, "locale": locale}
    )


def shape_for_speech(
    answer: str,
    *,
    user_message: str = "",
    max_sentences: int = 3,
    max_chars: int = 420,
) -> dict[str, Any]:
    """Adapt brain answer for speech (controller entry used by routes/runtime)."""
    pack = get_voice_presence().analyze(user_message, answer)
    spoken = str(pack.get("spoken") or "")
    if max_chars and len(spoken) > max_chars:
        spoken = spoken[: max_chars - 1].rsplit(" ", 1)[0]
        if spoken and spoken[-1] not in ".!?।":
            spoken += "." if pack.get("locale") != "hi" else "।"
        pack["spoken"] = spoken
        pack["spoken_tts"] = get_voice_presence().style.pace_for_tts(spoken)
        pack["trimmed"] = True
    return pack


def social_spoken_reply(user_message: str) -> str | None:
    """Deprecated mini-chatbot path — always None. Brain owns conversation."""
    return None


def strip_internal_chrome(text: str) -> str:
    """Remove agent / pipeline dump lines from a reply."""
    t = (text or "").strip()
    if not t:
        return ""
    if _INTERNAL_LEAK.search(t):
        return ""
    lines = []
    for line in t.splitlines():
        low = line.strip().lower()
        if not low:
            continue
        if low.startswith(("agent[", "agent goal[", "collaboration:", "routing →")):
            continue
        if "knowledge investigation required" in low:
            continue
        if "retrieve context" in low or "retrieve information" in low:
            continue
        lines.append(line.strip())
    return " ".join(lines).strip()


def is_garbage_spoken(answer: str) -> bool:
    low = (answer or "").strip().lower()
    if not low:
        return True
    if _INTERNAL_LEAK.search(low):
        return True
    if low.count("agent[") >= 1:
        return True
    if any(b in low for b in _GARBAGE_MARKERS):
        return True
    if "understand" in low and ("hindi" in low or "language" in low):
        return True
    # Ellipsis/punctuation-only padding — not a real reply
    words = [w for w in re.findall(r"[a-zA-Z\u0900-\u097F']+", low) if w not in {"a", "an", "the"}]
    if len(words) <= 3 and re.fullmatch(r"[\w\s.…]+", low or ""):
        # Short ack fragments like "Haan Sir..." / "Haan. . ."
        if words and words[0] in {"haan", "ji", "ok", "okay", "yes", "sir"}:
            return True
    if re.fullmatch(r"(haan|ji|ok|okay|yes)([\s.…]*(sir|ji)?)[\s.…]*", low or ""):
        return True
    return False


def soft_listening_fallback(
    *,
    locale: str = "en",
    user_message: str = "",
    context: dict[str, Any] | None = None,
    emotion: str | None = None,
    conversation_state: dict[str, Any] | None = None,
    response_engine=None,
) -> str:
    """Dynamic recovery — live generate first, then signal-composed line."""
    context = dict(context or {})
    conversation_state = conversation_state or {}
    emotion = emotion or context.get("emotion") or "neutral"

    if response_engine:
        try:
            result = response_engine.generate(
                intent="conversation_recovery",
                user_message=user_message,
                language=locale,
                emotion=emotion,
                context=context,
                state=conversation_state,
                style="natural_human_companion",
            )
            if result and not is_garbage_spoken(str(result)):
                return str(result).strip()
        except Exception:
            pass

    # Live brain recovery (dynamic — not a template library)
    live = _live_recovery_generate(user_message, locale=locale, emotion=str(emotion), context=context)
    if live and not is_garbage_spoken(live) and len(re.findall(r"[A-Za-z\u0900-\u097F]+", live)) >= 5:
        return live

    if context.get("last_response") and not is_garbage_spoken(str(context["last_response"])):
        return str(context["last_response"])

    return _compose_from_signals(user_message, locale=locale, emotion=str(emotion), context=context)


def _live_recovery_generate(
    user_message: str,
    *,
    locale: str,
    emotion: str,
    context: dict[str, Any],
) -> str:
    """Ask the production chat path for a one-line companion recovery."""
    try:
        from om_ai.runtime.chat_backend import chat_reply

        lang = "warm Hinglish" if locale == "hi" else "calm spoken English"
        system = (
            "You are OM, a loyal spoken companion (Jarvis-like). "
            f"Reply in {lang}, 1 short sentence only. "
            "No chatbot phrases. No 'how can I help'. No markdown. "
            f"User emotion signal: {emotion}."
        )
        topic = str(context.get("topic") or context.get("purpose") or "").strip()
        if topic:
            system += f" Active topic: {topic}."
        messages = [
            {"role": "system", "content": system[:900]},
            {"role": "user", "content": (user_message or "I'm here.")[:500]},
        ]
        reply, _info = chat_reply(messages, local_chat=None, local_loaded=False, native_chat=None)
        return str(reply or "").strip()
    except Exception:
        return ""


def _intent_signals(user_message: str) -> set[str]:
    low = (user_message or "").lower()
    signals: set[str] = set()
    if re.search(r"(?i)\b(hello|hi|hey|namaste|good morning|good evening)\b", low):
        signals.add("greeting")
    if re.search(r"(?i)\b(thank|thanks|shukriya|dhanyavad)\b", low):
        signals.add("thanks")
    if re.search(
        r"(insaan|human|natural|robot|machine|chatbot|bot\b|baat\s+nahi|"
        r"tarah\s+baat|normal\s+baat|jaise\s+insaan)",
        low,
    ):
        signals.add("meta_human")
    if re.search(r"(?i)\b(continue|us[ei]|wahi|pehle|keep going)\b", low):
        signals.add("continue")
    if re.search(r"(?i)\b(stop|ruk|band|chup|bas)\b", low):
        signals.add("stop")
    if not signals:
        signals.add("open")
    return signals


def _compose_from_signals(
    user_message: str,
    *,
    locale: str,
    emotion: str,
    context: dict[str, Any],
) -> str:
    """Last-resort compositional reply from live signals — not a script catalog."""
    signals = _intent_signals(user_message)
    hi = locale == "hi" or bool(
        re.search(r"\b(tum|nahi|nahin|kya|baat|insaan|tarah|sakte|bolo|mujhe|hai|ji)\b", (user_message or "").lower())
    )
    topic = str(context.get("topic") or "").replace("_", " ").strip()
    parts: list[str] = []

    if hi:
        if "meta_human" in signals:
            parts.append("Haan Sir... bilkul")
            parts.append("main natural baat karunga")
        elif "greeting" in signals:
            parts.append("Ji Sir... main yahan hoon")
        elif "thanks" in signals:
            parts.append("Hamesha Sir")
        elif emotion in {"frustration", "stress", "sad", "urgency"}:
            parts.append("Samajh gaya Sir")
        else:
            parts.append("Ji Sir... samajh gaya")
        if "continue" in signals and topic:
            parts.append(f"pehle wali {topic} pe chalte hain")
        elif "meta_human" in signals:
            parts.append("boliye kya karna hai")
        elif "thanks" not in signals and "stop" not in signals:
            parts.append("boliye aage kya karna hai")
    else:
        if "meta_human" in signals:
            parts.append("Fair point Sir")
            parts.append("I'll keep it natural")
        elif "greeting" in signals:
            parts.append("Yes Sir... I'm here")
        elif "thanks" in signals:
            parts.append("Anytime Sir")
        elif emotion in {"frustration", "stress", "sad", "urgency"}:
            parts.append("I hear you Sir")
        else:
            parts.append("Sir... I understand")
        if "continue" in signals and topic:
            parts.append(f"continuing {topic}")
        elif "meta_human" in signals:
            parts.append("what should we work on")
        elif "thanks" not in signals and "stop" not in signals:
            parts.append("tell me what you want next")

    # Join with natural pauses
    if len(parts) == 1:
        return parts[0] + ("." if not hi else ".")
    if len(parts) == 2:
        return f"{parts[0]}... {parts[1]}."
    return f"{parts[0]}... {parts[1]} — {parts[2]}."


def rescue_spoken(user_message: str, bad_answer: str = "") -> str:
    """Soft listening fallback when spoken text is unusable."""
    del bad_answer
    locale = detect_speech_locale(user_message)
    emotion = get_voice_presence().emotion.detect(user_message)
    line = soft_listening_fallback(
        locale=locale,
        user_message=user_message,
        emotion=emotion,
        context={"user_message": user_message, "emotion": emotion},
    )
    if line and not is_garbage_spoken(line):
        return line
    return _compose_from_signals(
        user_message,
        locale=locale,
        emotion=str(emotion),
        context={},
    )
