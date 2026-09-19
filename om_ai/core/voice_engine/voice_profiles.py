"""Voice profile settings — free system default, paid neural optional."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class VoiceProfile:
    name: str
    provider: str
    voice_id: str | None = None
    language: str = "en"
    accent: str = "neutral"
    gender: str = "male"
    style: str = "calm_ai"
    pace_wpm: int = 140
    pitch: float = 0.0
    stability: float = 0.8
    similarity: float = 0.75
    emotion: str = "calm"
    description: str = ""
    free: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OMVoiceProfile:
    """Human Indian-male companion settings (Aman-style / neural optional)."""

    name: str = "OM Aman"
    gender: str = "male"
    accent: str = "indian_english"
    language: str = "hi-en"
    pitch: float = 0.96
    speed: float = 1.0
    stability: float = 0.58
    similarity: float = 0.82
    style_exaggeration: float = 0.38
    emotion: str = "calm"
    style: str = "warm clear Indian male companion — natural pace, human feel"

    def update(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def elevenlabs_settings(self) -> dict[str, Any]:
        return {
            "stability": float(self.stability),
            "similarity_boost": float(self.similarity),
            "style": float(self.style_exaggeration),
            "use_speaker_boost": True,
        }


def jarvis_butler_profile() -> OMVoiceProfile:
    return OMVoiceProfile()


class VoiceProfiles:
    """Dynamic OM voice registry. Default = free macOS Aman (Indian male)."""

    DEFAULT = "om_system"

    def __init__(self) -> None:
        self._profiles: dict[str, VoiceProfile] = {
            "om_system": VoiceProfile(
                name="OM Aman",
                provider="macos",
                voice_id="Aman",
                language="en-IN",
                accent="indian_english",
                gender="male",
                style="warm_human_companion",
                pace_wpm=178,
                pitch=0.0,
                emotion="calm",
                free=True,
                description="Free local macOS Aman — clear Indian male companion",
            ),
            "om_premium": VoiceProfile(
                name="OM Premium",
                provider="elevenlabs",
                voice_id=None,
                language="en-IN",
                accent="indian_english",
                gender="male",
                style="intelligent_ai_companion",
                pace_wpm=178,
                stability=0.58,
                similarity=0.82,
                emotion="calm",
                free=False,
                description="Optional paid neural Indian male companion voice",
            ),
            "om_hinglish": VoiceProfile(
                name="OM Hinglish",
                provider="elevenlabs",
                language="hi",
                accent="indian_english",
                gender="male",
                style="warm_companion",
                pace_wpm=178,
                stability=0.55,
                similarity=0.8,
                emotion="friendly",
                free=False,
                description="Optional paid Hindi / Hinglish neural voice",
            ),
            "om_professional": VoiceProfile(
                name="OM Professional",
                provider="azure",
                language="en-IN",
                accent="indian_english",
                gender="male",
                style="executive_assistant",
                pace_wpm=174,
                stability=0.7,
                emotion="focused",
                free=False,
                description="Optional Azure professional Indian English voice",
            ),
        }

    def get(self, name: str | None = None) -> dict[str, Any]:
        key = name or self.DEFAULT
        profile = self._profiles.get(key) or self._profiles[self.DEFAULT]
        return profile.to_dict()

    def register(self, profile: VoiceProfile) -> None:
        self._profiles[profile.name] = profile

    def available(self) -> list[str]:
        return list(self._profiles.keys())

    def free_profiles(self) -> list[str]:
        return [k for k, p in self._profiles.items() if p.free]

    def update(self, name: str, **changes: Any) -> dict[str, Any]:
        profile = self._profiles.get(name)
        if not profile:
            raise ValueError(f"Voice profile not found: {name}")
        for key, value in changes.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        return profile.to_dict()
