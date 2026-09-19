"""
OM Voice Presence Engine

Dynamic spoken conversation layer.
Never speak internal agent / pipeline chrome.
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
            spoken = soft_listening_fallback(locale=locale, user_message=user_message)
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
        # Drop whole dump — never read internal agent notes aloud
        return ""
    # Strip leftover debug prefixes if mixed into a longer reply
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
    bad = (
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
        "wasn't reliable",
        "ask again in one short",
        "how can i help you today",
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
    if any(b in low for b in bad):
        return True
    if "understand" in low and ("hindi" in low or "language" in low):
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

    """
    Dynamic fallback.

    No hardcoded replies.
    No script responses.

    Delegates generation to OM response intelligence.
    """

    context = context or {}
    conversation_state = conversation_state or {}


    if response_engine:

        result = response_engine.generate(

            intent="conversation_recovery",

            user_message=user_message,

            language=locale,

            emotion=emotion,

            context=context,

            state=conversation_state,

            style="natural_human_companion"

        )


        if result:

            return str(result).strip()



    # Last safety fallback:
    # Generate from available brain layer

    if context.get("last_response"):

        return context["last_response"]



    return ""


def rescue_spoken(user_message: str, bad_answer: str = "") -> str:
    """Soft listening fallback when spoken text is unusable."""
    del bad_answer
    locale = detect_speech_locale(user_message)
    return soft_listening_fallback(locale=locale, user_message=user_message)
