"""
Master free-path speech delivery — Indian male companion (Aman).

Natural pace + light emotion. Avoid heavy silence markers that sound robotic.
"""
from __future__ import annotations

import re
from typing import Any


# macOS `say -r` — conversational Indian English (Aman sounds best ~170–185)
NATURAL_RATE = 178
CALM_RATE = 168
SOFT_RATE = 162
EXCITED_RATE = 188
FOCUSED_RATE = 174


def humanize_text(text: str) -> str:
    """Strip TTS chrome / robotic phrasing; keep short conversational lines."""
    t = (text or "").strip()
    if not t:
        return t

    t = re.sub(r"\[\[slnc\s+\d+\]\]", " ", t, flags=re.I)
    t = re.sub(r"\[\[volm\s+[\d.]+\]\]", " ", t, flags=re.I)
    t = re.sub(r"\[\[rate\s+\d+\]\]", " ", t, flags=re.I)
    t = re.sub(r"\[\[pbas\s+[+\-]?\d+\]\]", " ", t, flags=re.I)
    t = re.sub(r"<break\s+\d+ms\s*/>", " ", t, flags=re.I)

    t = re.sub(r"```[\s\S]*?```", " ", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    t = re.sub(r"[*_#]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    for pat, repl in (
        (r"(?i)^certainly[,!]?\s*", ""),
        (r"(?i)^of course[,!]?\s*", ""),
        (r"(?i)^absolutely[,!]?\s*", ""),
        (r"(?i)^as an ai[, ]*", ""),
        (r"(?i)^i would be happy to\s+", "I'll "),
        (r"(?i)^i'd be happy to\s+", "I'll "),
    ):
        t = re.sub(pat, repl, t).strip()

    words = t.split()
    if len(words) > 55:
        parts = re.split(r"(?<=[.!?।])\s+", t)
        t = " ".join(p.strip() for p in parts[:3] if p.strip())

    return t.strip()


def _rate_for(emotion: str) -> int:
    e = (emotion or "calm").lower()
    if e in {"soft", "whisper"}:
        return SOFT_RATE
    if e in {"concerned", "tired", "sad"}:
        return CALM_RATE
    if e == "excited":
        return EXCITED_RATE
    if e in {"focused", "attentive"}:
        return FOCUSED_RATE
    return NATURAL_RATE


def _pitch_for(emotion: str) -> int:
    """macOS [[pbas]] — slight warmth for a real male companion."""
    e = (emotion or "calm").lower()
    if e in {"soft", "whisper", "concerned", "tired", "sad"}:
        return -1
    if e == "excited":
        return 1
    if e in {"focused", "attentive"}:
        return 0
    return 0


def apply_human_prosody(text: str, *, emotion: str = "calm") -> str:
    """
    Light conversational breath for Aman / Indian male system voice.
    Keep silences short — long [[slnc]] makes speech feel broken.
    """
    t = humanize_text(text)
    if not t:
        return t

    e = (emotion or "calm").lower()
    comma = 70
    stop = 140
    if e in {"concerned", "soft", "whisper", "tired", "sad"}:
        comma, stop = 95, 175
    elif e == "excited":
        comma, stop = 55, 110
    elif e in {"focused", "attentive"}:
        comma, stop = 65, 130

    # Soft beat after Sir mid-phrase only
    t = re.sub(
        r"(?i)\b(sir|ji)\b([,])(\s+)",
        rf"\1\2 [[slnc {comma}]] \3",
        t,
    )
    t = re.sub(r"([.!?])\s+", rf"\1 [[slnc {stop}]] ", t)
    t = re.sub(r"(।)\s*", rf"\1 [[slnc {stop}]] ", t)
    t = re.sub(r"([;:])\s+", rf"\1 [[slnc {comma}]] ", t)

    rate = _rate_for(e)
    pitch = _pitch_for(e)
    vol = ""
    if e == "whisper":
        vol = " [[volm 0.45]]"
    elif e in {"soft", "concerned"}:
        vol = " [[volm 0.88]]"
    elif e == "excited":
        vol = " [[volm 1.0]]"

    prefix = f"[[rate {rate}]]"
    if pitch:
        prefix += f" [[pbas {pitch:+d}]]"
    prefix += vol

    t = re.sub(r"(\[\[slnc\s+\d+\]\]\s*){2,}", rf"[[slnc {stop}]] ", t, flags=re.I)
    return f"{prefix} {t}".strip()


def delivery_plan(text: str, *, emotion: str = "calm") -> dict[str, Any]:
    spoken = apply_human_prosody(text, emotion=emotion)
    clean = humanize_text(text)
    rate = _rate_for(emotion)
    return {
        "spoken_tts": spoken,
        "spoken_clean": clean,
        "rate": rate,
        "emotion": emotion,
        "voice": "Aman",
        "accent": "indian_english",
        "engine": "macos_say",
        "human_ceiling": "system_tts",
        "browser_rate": round(rate / 178.0, 3),
        "note": "Free Aman (Indian male) system voice — paced for clear conversation.",
    }
