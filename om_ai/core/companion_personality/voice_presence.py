"""Shape spoken replies so OM feels present — Jarvis-like conversation, not TTS essays.

Supports English + Hindi / Hinglish the way a friend would talk.
"""
from __future__ import annotations

import re
from typing import Any


_JARVIS_VOICE_HINT = """
You are OM — speaking exactly like Jarvis to Tony Stark:
calm British butler energy, sharp, loyal, warm, always one step ahead.

This is a LIVE voice call. You are not reading a script or a chatbot reply.

Address the user as Sir (English) or Sir / Ji (Hinglish) naturally — not every word, but often.
Always end with a short invitation to continue: ask what they need, how they feel, or what to do next.

Language:
- Mirror the user. Hindi/Hinglish in → warm Hinglish out. English in → polished spoken English.
- Never ask them to "rephrase in one short sentence".
- Never sound like a FAQ or a document.

Spoken style:
- 1–3 short sentences max.
- Acknowledge → answer → ask one real question back.
- Phrases that fit: "Of course, Sir.", "Right away.", "Haan sir — boliye.", "Kya baat hai?", "Shall I proceed?"
- No markdown, bullets, code, or "As an AI…".
""".strip()



_ROBOTIC = [
    (re.compile(r"(?i)^as an ai[, ]*"), ""),
    (re.compile(r"(?i)^certainly[,!]?\s*i('d| would) be happy to\s*"), ""),
    (re.compile(r"(?i)^of course[,!]?\s*"), ""),
    (re.compile(r"(?i)^sure[,!]?\s*i can help (you )?with that[.!]?\s*"), "Sure. "),
    (re.compile(r"(?i)how can i (assist|help) you( today)?\??"), "What should we take on?"),
    (re.compile(r"(?i)is there anything else i can help you with\??"), "Anything else on your mind?"),
    (re.compile(r"(?i)please let me know if you (need|have) .*"), ""),
    (re.compile(r"(?i)i want to help\s*[—\-–,]?\s*could you rephrase.*"), ""),
    (re.compile(r"(?i)please rephrase.*(short|plain).*"), ""),
]


_DEVANAGARI = re.compile(r"[\u0900-\u097F]")

# Common Hinglish / roman Hindi social cues
_HINGLISH_CUES = re.compile(
    r"(?i)\b("
    r"haan|han|haa|haanji|hanji|ji|bhai|yaar|yar|boss|dada|"
    r"kaise|kese|kaisa|kaisi|ho|hai|hain|bolo|batao|bata|sun|suno|"
    r"kya|kyu|kyun|kyunki|nahi|nahin|mat|theek|thik|achha|acha|accha|"
    r"namaste|namaskar|shukriya|dhanyavad|please\s*yaar|"
    r"kya\s*haal|sab\s*theek|mast|chalo|kar\s*do|kar\s*dena|"
    r"mujhe|mujhse|tum|aap|mera|meri|tumhara"
    r")\b"
)

# Web Speech hi-IN often writes English as Devanagari phonetics
_PHONETIC_DEV_EN = (
    (re.compile(r"व्हाट\s*आर\s*यू\s*डूइंग|व्हाट\s*आर\s*यू\s*डूइङ|व्हाट्स?\s*अप"), "what are you doing"),
    (re.compile(r"हाउ\s*आर\s*यू|हाउ\s*आर्\s*यू"), "how are you"),
    (re.compile(r"हू\s*आर\s*यू|हू\s*आर\s*यु"), "who are you"),
    (re.compile(r"व्हाट\s*आर\s*यू|वॉट\s*आर\s*यू"), "what are you"),
    (re.compile(r"गुड\s*मॉर्निंग|गुड\s*मॉरनिंग"), "good morning"),
    (re.compile(r"गुड\s*नाइट|गुड\s*नाईट"), "good night"),
    (re.compile(r"थैंक\s*यू|थैंक्स|थैङ्क\s*यू"), "thank you"),
    (re.compile(r"हैलो|हेलो|हाय|हेय"), "hello"),
    (re.compile(r"येस|यस"), "yes"),
    (re.compile(r"नो|नॉट"), "no"),
    (re.compile(r"ओके|ओ\.?के"), "ok"),
    (re.compile(r"प्लीज|प्लीज़"), "please"),
    (re.compile(r"हेल्प|हेल्‍प"), "help"),
    (re.compile(r"स्टॉप|स्टाप"), "stop"),
)


def normalize_heard_text(text: str) -> str:
    """Map hi-IN phonetic English (Devanagari) back to Latin for intent matching."""
    raw = (text or "").strip()
    if not raw:
        return ""
    for pat, repl in _PHONETIC_DEV_EN:
        if pat.search(raw):
            return repl
    return raw


def detect_speech_locale(user_message: str) -> str:
    """Return 'hi' for Hindi/Hinglish, else 'en'."""
    text = normalize_heard_text(user_message) or (user_message or "")
    # Pure phonetic-English Devanagari already normalized to Latin → English
    if text != (user_message or "").strip() and not _DEVANAGARI.search(text):
        return "en"
    if _DEVANAGARI.search(text):
        # If it's mostly phonetic English leftovers, still check cues
        if any(p.search(user_message or "") for p, _ in _PHONETIC_DEV_EN):
            return "en"
        return "hi"
    if _HINGLISH_CUES.search(text):
        return "hi"
    return "en"


def jarvis_system_hint(*, conversation_mode: str = "assist", locale: str = "en") -> str:
    lang = (
        "User is speaking Hindi/Hinglish — reply in warm respectful Hinglish. "
        "Use Sir / Ji. Example vibe: 'Haan sir, bilkul. Boliye — kya baat hai?'"
        if locale == "hi"
        else "User is speaking English — reply in calm Jarvis English. "
        "Address them as Sir. End with a short question."
    )
    return f"{_JARVIS_VOICE_HINT}\n{lang}\nConversation mode: {conversation_mode}."


def _strip_markdown(text: str) -> str:
    t = text or ""
    t = re.sub(r"```[\s\S]*?```", " ", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"[*_#>]+", " ", t)
    t = re.sub(r"(?m)^\s*[-•]\s+", "", t)
    t = re.sub(r"(?m)^\s*\d+[.)]\s+", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?।])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def shape_for_speech(
    answer: str,
    *,
    user_message: str = "",
    max_sentences: int = 3,
    max_chars: int = 420,
) -> dict[str, Any]:
    raw = (answer or "").strip()
    display = raw
    spoken = _strip_markdown(raw)
    locale = detect_speech_locale(user_message)

    for pat, repl in _ROBOTIC:
        spoken = pat.sub(repl, spoken).strip()

    spoken = spoken.replace(" ; ", ". ")
    if locale != "hi":
        spoken = spoken.replace(" — ", ". ").replace(" - ", ". ")

    sents = _sentences(spoken)
    if not sents or is_garbage_spoken(spoken):
        spoken = rescue_spoken(user_message)
        return {
            "spoken": spoken,
            "spoken_tts": _pace(spoken),
            "display": spoken,
            "trimmed": False,
            "locale": locale,
        }

    trimmed = False
    if len(sents) > max_sentences:
        sents = sents[:max_sentences]
        trimmed = True
    spoken = " ".join(sents)
    if len(spoken) > max_chars:
        spoken = spoken[: max_chars - 1].rsplit(" ", 1)[0] + ("।" if locale == "hi" else ".")
        trimmed = True

    return {
        "spoken": spoken,
        "spoken_tts": _pace(spoken),
        "display": display if display else spoken,
        "trimmed": trimmed,
        "locale": locale,
    }


def _pace(spoken: str) -> str:
    """Jarvis cadence: slower breath between clauses — not machine-gun TTS."""
    t = (spoken or "").strip()
    # Don't double-pace if already marked
    if "[[slnc" in t.lower():
        return t
    t = re.sub(r"\s*—\s*", " [[slnc 220]] ", t)
    t = re.sub(r"\s*-\s+", " [[slnc 160]] ", t)
    t = re.sub(r"([,;:])\s+", r"\1 [[slnc 240]] ", t)
    t = re.sub(r"([.!?])\s+", r"\1 [[slnc 480]] ", t)
    t = re.sub(r"(।)\s*", r"\1 [[slnc 420]] ", t)
    # Soft pause after Sir / sir for butler feel
    t = re.sub(r"(?i)\b(sir)\b([,.!]?)(\s+)", r"\1\2 [[slnc 180]] \3", t)
    return t.strip()


def social_spoken_reply(user_message: str) -> str | None:
    """Fast human / Jarvis presence beats — English + Hindi/Hinglish."""
    original = (user_message or "").strip()
    raw = normalize_heard_text(original) or original
    if not raw:
        return "Haan sir — main yahin hoon. Boliye, kya baat hai?"
    low = raw.lower().strip()
    locale = detect_speech_locale(original)
    if raw != original and not _DEVANAGARI.search(raw):
        locale = "en"
    words = low.split()

    # English first when STT wrote English as Devanagari phonetics
    if locale == "en":
        if low in {"hi", "hey", "hello", "hii", "hiii", "yo"}:
            return "Good to hear you, Sir. I'm right here — what shall we take on?"
        if "good morning" in low or low == "morning":
            return "Good morning, Sir. Systems ready. How may I help you today?"
        if "good night" in low or "goodnight" in low:
            return "Good night, Sir. Rest well — I'll be here when you need me."
        if "thank" in low:
            return "Always, Sir. Anything else on your mind?"
        if low in {"how are you", "how are you?", "how's it going", "hows it going"}:
            return "I'm well, Sir — fully focused on you. What do you need right now?"
        if low in {"who are you", "what are you"}:
            return (
                "I'm OM, Sir — your personal companion, in the spirit of Jarvis. "
                "Talk freely. What would you like first?"
            )
        if "what are you doing" in low or low in {"what doing", "whatcha doing"}:
            return (
                "Standing by with you, Sir — listening. "
                "Shall we work on something, or would you rather just talk?"
            )
        if re.search(r"(?i)\b(are you (there|listening)|can you hear me)\b", low):
            return "Yes, Sir — I'm here and listening. Please, go ahead."
        if any(k in low for k in ("tired", "exhausted", "burned out", "burnt out")):
            return (
                "I hear you, Sir. That sounds heavy. "
                "Would you like to talk it through, or shall I take something off your plate?"
            )
        if any(k in low for k in ("stressed", "anxious", "overwhelmed", "pressure")):
            return (
                "Alright, Sir — slow down with me for a second. "
                "What's the one thing weighing on you most?"
            )
        if "spent all night" in low or "all night" in low:
            return (
                "That's a long stretch, Sir. Respect. "
                "A short break plan, or straight into the problem?"
            )
        if len(words) <= 12 and low:
            # Still English social — avoid falling into Hindi catch-all
            if "what" in low and "doing" in low:
                return (
                    "Standing by with you, Sir — listening. "
                    "Shall we work on something, or would you rather just talk?"
                )

    # Hindi / Hinglish — only real Hindi (not phonetic English)
    if locale == "hi" or (_DEVANAGARI.search(original) and raw == original):
        if (
            "हिंदी" in original
            or "हिन्दी" in original
            or re.search(r"(?i)\bhindi\b", low)
        ) and (
            any(x in original for x in ("आती", "आता", "बोल", "समझ", "जान"))
            or re.search(r"(?i)\b(know|speak|understand|aat[ie]|aata)\b", low)
        ):
            return (
                "Haan sir, bilkul. Hindi aur Hinglish dono aati hai. "
                "Aap natural boliye — main samajhta hoon. Ab kya baat hai?"
            )
        if any(
            x in original
            for x in (
                "क्या कहना चाहते",
                "क्या बोलना चाहते",
                "क्या कहना है",
                "क्या बोलना है",
            )
        ) or re.search(r"(?i)\b(kya\s+kehna|kya\s+bolna)\b", low):
            return (
                "Sir, jo mann mein hai wahi boliye. "
                "Main sun raha hoon — tension mat lijiye. Kya share karna hai?"
            )
        if any(x in original for x in ("क्या कर रहे", "क्या कर रहा", "क्या हो रहा")) or re.search(
            r"(?i)\b(kya\s+kar\s+rahe|kya\s+ho\s+raha)\b", low
        ):
            return (
                "Aapke saath hoon sir — sun raha hoon, ready. "
                "Boliye, aaj kya handle karna hai?"
            )
        if any(x in original for x in ("कौन हो", "तुम कौन", "आप कौन")) or re.search(
            r"(?i)\b(tum\s+kaun|aap\s+kaun)\b", low
        ):
            return (
                "Main OM hoon sir — aapka personal companion, Jarvis jaisa. "
                "Aap mujhse kuch bhi poochhiye. Pehle kya baat karni hai?"
            )
        if re.search(r"(?i)\b(namaste|namaskar)\b", low) or "नमस्ते" in original:
            return "Namaste sir. Main OM — hazir hoon. Boliye, kya seva karun?"
        if re.search(
            r"(?i)\b(han|haan|haa|hanji|haanji)\b.*\b(bhai|yaar|sir)?\b.*\b(bolo|batao)?\b|"
            r"\b(kaise|kese)\s+ho\b|\bkya\s+haal\b|\bsab\s+theek\b|"
            r"\bbolo\s+kaise\b|\bhan\s+bhai\b|\bhaan\s+sir\b",
            low,
        ) or any(x in original for x in ("कैसे हो", "कैसी हो", "क्या हाल")):
            return (
                "Bilkul theek hoon sir — aapke liye ready. "
                "Aap sunaiye, kya chal raha hai? Kaam, tension, ya bas baat?"
            )
        if re.search(r"(?i)\b(kaise|kese)\s+(ho|hai)\b", low):
            return "Main bilkul theek sir. Aap kaise hain — aur aaj kya madad chahiye?"
        if re.search(r"(?i)\b(shukriya|dhanyavad|thanks|thank\s*you)\b", low) or "शुक्रिया" in original:
            return "Hamesha sir. Aur kuch? Main yahin hoon."
        if re.search(r"(?i)\b(theek|thik)\s*(hai|ho)\b", low):
            return "Theek hai sir. Main sun raha hoon — aage boliye, kya karna hai?"
        if re.search(r"(?i)\b(acha|achha|accha|sahi)\b", low) and len(words) <= 4:
            return "Hmm, samajh gaya sir. Ab boliye — next kya?"
        if re.search(r"(?i)\b(madad|help|jarurat|zarurat)\b", low):
            return "Haan sir, bataiye. Main hun na — kya problem hai pehle?"
        if re.search(r"(?i)\b(thak|thaka|thaki|tired)\b", low) or "थक" in original:
            return (
                "Samajh gaya sir — thakaan lag rahi hai. "
                "Baat karni hai, ya main kuch kaam sambhaluun aapke liye?"
            )
        if re.search(r"(?i)\b(pareshan|tension|stress)\b", low) or "परेशान" in original:
            return (
                "Theek hai sir — ek second. "
                "Sabse badi baat kaunsi hai? Wahi pehle, main saath hoon."
            )
        if re.search(r"(?i)\b(sun|suno|sun\s*rahe|listening)\b", low) or "सुन" in original:
            return "Haan sir, bilkul sun raha hoon. Boliye — kya baat hai?"
        if re.search(r"(?i)\b(baat\s*kar\w*|baat\s*kro|talk\s+to\s+me|bolo\s*na)\b", low) or "बात" in original:
            return (
                "Zaroor sir. Main aapse baat karne ke liye yahin hoon. "
                "Aaj dil pe kya hai — kaam, plan, ya kuch personal?"
            )
        if _DEVANAGARI.search(original) and len(original) <= 90 and raw == original:
            return (
                "Haan sir, sun liya. Main aapke saath hoon. "
                "Boliye — kaam hai, sawaal hai, ya bas baat karni hai?"
            )

    return None


def is_garbage_spoken(answer: str) -> bool:
    low = (answer or "").strip().lower()
    if not low:
        return True
    bad = (
        "rephrase",
        "one short sentence",
        "short sentence",
        "plain words",
        "as an ai",
        "i'm just a language model",
        "i cannot",
        "i can't assist with that",
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
    )
    if any(b in low for b in bad):
        return True
    if "understand" in low and ("hindi" in low or "language" in low):
        return True
    return False


def rescue_spoken(user_message: str, bad_answer: str = "") -> str:
    social = social_spoken_reply(user_message)
    if social:
        return social
    locale = detect_speech_locale(user_message)
    if locale == "hi":
        if len((user_message or "").split()) <= 14:
            return (
                "Samajh gaya sir. Main aapke saath hoon — "
                "boliye clearly kya chahiye, main kar deta hoon. Kya priority hai?"
            )
        return (
            "Theek hai sir, context mil gaya. "
            "Result kya chahiye? Main uspe kaam karta hoon — bataiye."
        )
    if len((user_message or "").split()) <= 12:
        return "I'm with you, Sir. Tell me what you need — I'll handle it. What comes first?"
    return "Got it, Sir. What outcome do you want — I'll work from there?"
