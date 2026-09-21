"""
Dynamic free-path speech delivery — Indian male companion (Aman).

Prosody (rate / pause / pitch) is derived from emotion + text structure,
not a single fixed template.
"""
from __future__ import annotations

import re
from typing import Any


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
        (r"(?i)^i can help with that[.!]?\s*", ""),
        (r"(?i)share one more detail[^.]*\.?", ""),
    ):
        t = re.sub(pat, repl, t).strip()

    words = t.split()
    # Dynamic trim: tighter when excited/urgent feel; allow more when soft
    ceiling = 55
    if len(words) > ceiling:
        parts = re.split(r"(?<=[.!?।])\s+", t)
        t = " ".join(p.strip() for p in parts[:3] if p.strip())

    return t.strip()


def _text_metrics(text: str) -> dict[str, Any]:
    t = text or ""
    words = len(t.split())
    stops = sum(t.count(c) for c in ".!?।")
    commas = t.count(",")
    ellipsis = t.count("...")
    dev = len(re.findall(r"[\u0900-\u097F]", t))
    return {
        "words": words,
        "stops": stops,
        "commas": commas,
        "ellipsis": ellipsis,
        "devanagari_ratio": (dev / max(1, len(t))),
        "question": "?" in t or "؟" in t,
    }


def _rate_for(emotion: str, metrics: dict[str, Any]) -> int:
    """Base emotion rate, nudged by length and script density."""
    e = (emotion or "calm").lower()
    base = {
        "soft": 162,
        "whisper": 158,
        "concerned": 168,
        "tired": 165,
        "sad": 164,
        "excited": 188,
        "focused": 174,
        "attentive": 174,
        "warm": 176,
        "urgency": 184,
        "frustration": 170,
        "stress": 166,
    }.get(e, 178)

    words = int(metrics.get("words") or 0)
    if words > 40:
        base -= 6
    elif words < 8:
        base += 4
    if float(metrics.get("devanagari_ratio") or 0) > 0.25:
        base -= 4  # clearer Hindi pacing
    if metrics.get("question"):
        base -= 2
    return max(150, min(195, base))


def _pitch_for(emotion: str) -> int:
    e = (emotion or "calm").lower()
    if e in {"soft", "whisper", "concerned", "tired", "sad", "stress"}:
        return -1
    if e in {"excited", "happy"}:
        return 1
    return 0


def _pause_ms(emotion: str, metrics: dict[str, Any]) -> tuple[int, int]:
    """Return (comma_ms, stop_ms) from emotion + sentence density."""
    e = (emotion or "calm").lower()
    comma, stop = 70, 140
    if e in {"concerned", "soft", "whisper", "tired", "sad", "stress"}:
        comma, stop = 95, 175
    elif e in {"excited", "urgency"}:
        comma, stop = 55, 110
    elif e in {"focused", "attentive"}:
        comma, stop = 65, 130
    # More stops → slightly shorter gaps so it doesn't drag
    stops = int(metrics.get("stops") or 0)
    if stops >= 3:
        stop = max(100, stop - 20)
        comma = max(45, comma - 10)
    if metrics.get("ellipsis"):
        comma += 15
    return comma, stop


def apply_human_prosody(text: str, *, emotion: str = "calm") -> str:
    """Conversational breath for Aman — pauses/rate follow live text metrics."""
    t = humanize_text(text)
    if not t:
        return t

    metrics = _text_metrics(t)
    e = (emotion or "calm").lower()
    comma, stop = _pause_ms(e, metrics)

    t = re.sub(
        r"(?i)\b(sir|ji)\b([,])(\s+)",
        rf"\1\2 [[slnc {comma}]] \3",
        t,
    )
    # Dynamic ellipsis → short breath (protect before per-dot rules)
    t = t.replace("…", "...")
    t = re.sub(r"\.{3,}", "«ELLIP»", t)
    t = re.sub(r"([.!?])\s+", rf"\1 [[slnc {stop}]] ", t)
    t = re.sub(r"(।)\s*", rf"\1 [[slnc {stop}]] ", t)
    t = re.sub(r"([;:])\s+", rf"\1 [[slnc {comma}]] ", t)
    t = t.replace("«ELLIP»", f" [[slnc {comma + 20}]] ")

    rate = _rate_for(e, metrics)
    pitch = _pitch_for(e)
    vol = ""
    if e == "whisper":
        vol = " [[volm 0.45]]"
    elif e in {"soft", "concerned", "stress"}:
        vol = " [[volm 0.88]]"
    elif e in {"excited", "urgency"}:
        vol = " [[volm 1.0]]"

    prefix = f"[[rate {rate}]]"
    if pitch:
        prefix += f" [[pbas {pitch:+d}]]"
    prefix += vol

    t = re.sub(r"(\[\[slnc\s+\d+\]\]\s*){2,}", rf"[[slnc {stop}]] ", t, flags=re.I)
    return f"{prefix} {t}".strip()


def delivery_plan(text: str, *, emotion: str = "calm") -> dict[str, Any]:
    clean = humanize_text(text)
    metrics = _text_metrics(clean)
    rate = _rate_for(emotion, metrics)
    spoken = apply_human_prosody(text, emotion=emotion)
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
        "metrics": metrics,
        "note": f"Dynamic Aman delivery · rate={rate} · emotion={emotion}",
    }
