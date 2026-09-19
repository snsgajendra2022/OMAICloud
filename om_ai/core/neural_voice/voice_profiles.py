from __future__ import annotations

PROFILES = {
    "jarvis_butler": {
        "provider": "elevenlabs",
        "style": "british_butler",
        "pace_wpm": 132,
        "description": "Calm professional companion voice",
    },
    "om_calm": {
        "provider": "system",
        "voice": "Daniel",
        "pace_wpm": 132,
    },
}

class VoiceProfiles:
    def get(self, name: str = "jarvis_butler") -> dict:
        return dict(PROFILES.get(name) or PROFILES["om_calm"])
