"""STEP 4 — Lip sync frames / visemes for 3D avatar + HUD orb."""
from __future__ import annotations

import re
from typing import Any

# Approximate viseme classes for procedural jaw / mouth shapes
_VISEME_MAP = {
    "silence": 0.02,
    "PP": 0.08,  # p/b/m
    "FF": 0.12,  # f/v
    "TH": 0.14,  # th
    "DD": 0.16,  # t/d/n/l
    "kk": 0.18,  # k/g
    "CH": 0.2,  # ch/j/sh
    "SS": 0.15,  # s/z
    "nn": 0.12,
    "RR": 0.14,
    "aa": 0.28,  # open vowels
    "E": 0.2,
    "I": 0.14,
    "O": 0.26,
    "U": 0.18,
}


def _viseme_for_token(tok: str) -> str:
    t = re.sub(r"[^a-zA-Z]", "", tok).lower()
    if not t:
        return "silence"
    c = t[0]
    if c in "bpm":
        return "PP"
    if c in "fv":
        return "FF"
    if t.startswith("th"):
        return "TH"
    if c in "tdnl":
        return "DD"
    if c in "kgcq":
        return "kk"
    if t.startswith(("ch", "sh", "j")):
        return "CH"
    if c in "sz":
        return "SS"
    if c in "r":
        return "RR"
    if c in "aeiou":
        if c in "a":
            return "aa"
        if c in "e":
            return "E"
        if c in "i":
            return "I"
        if c in "o":
            return "O"
        return "U"
    return "DD"


class LipSyncEngine:
    """Builds timed mouth/jaw frames from spoken text (works without paid TTS)."""

    def from_text(self, text: str, *, emotion: str = "calm", fps: int = 20) -> dict[str, Any]:
        clean = re.sub(r"\[\[slnc\s+\d+\]\]", " ", text or "", flags=re.I)
        clean = re.sub(r"<break\s+\d+ms\s*/>", " ", clean, flags=re.I)
        clean = re.sub(r"\s+", " ", clean).strip()
        words = clean.split() or [""]
        emotion_scale = {
            "excited": 1.25,
            "calm": 1.0,
            "soft": 0.75,
            "whisper": 0.55,
            "concerned": 0.85,
            "focused": 0.95,
        }.get((emotion or "calm").lower(), 1.0)

        frames: list[dict[str, Any]] = []
        t = 0.0
        dt = 1.0 / max(8, fps)
        for w in words[:80]:
            vis = _viseme_for_token(w)
            jaw = min(0.42, _VISEME_MAP.get(vis, 0.16) * emotion_scale)
            # 2–3 subframes per word for smoother jaw
            for i in range(3):
                open_amt = jaw * (0.55 + 0.45 * (1 if i == 1 else 0.7))
                frames.append(
                    {
                        "t": round(t, 3),
                        "viseme": vis if i == 1 else "silence",
                        "jaw": round(open_amt, 3),
                        "mouth": round(open_amt * 0.9, 3),
                    }
                )
                t += dt
            # slight close between words
            frames.append(
                {"t": round(t, 3), "viseme": "silence", "jaw": 0.04, "mouth": 0.03}
            )
            t += dt * 0.5

        peaks = [f["jaw"] for f in frames]
        return {
            "mode": "viseme",
            "fps": fps,
            "duration_s": round(t, 3),
            "frames": frames,
            "peaks": peaks,
            "emotion": emotion,
        }

    def jaw_at(self, lips: dict[str, Any], elapsed_s: float) -> float:
        frames = lips.get("frames") or []
        if not frames:
            return 0.02
        cur = frames[0]
        for f in frames:
            if float(f.get("t", 0)) <= elapsed_s:
                cur = f
            else:
                break
        return float(cur.get("jaw") or 0.02)

    def envelope(self, text: str) -> dict[str, Any]:
        """Compat with older avatar LipSync.envelope()."""
        pack = self.from_text(text)
        return {
            "frames": pack["peaks"],
            "mode": "energy",
            "visemes": "approx",
            "lips": pack,
        }
