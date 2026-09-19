"""STEP 53 — Voice Engine (single source of truth for companion TTS)."""
from __future__ import annotations

from .emotion_voice import EmotionVoice
from .human_delivery import apply_human_prosody, delivery_plan, humanize_text
from .lip_sync import LipSyncEngine
from .prosody_engine import ProsodyEngine
from .realtime_tts import RealtimeTTS
from .streaming_voice import StreamingVoice
from .tts_provider import TTSProvider, VoiceProvider, active_provider, get_voice_engine
from .voice_cloner import VoiceCloner
from .voice_model import NeuralTTS, VoiceModel
from .voice_profiles import (
    OMVoiceProfile,
    VoiceProfile,
    VoiceProfiles,
    jarvis_butler_profile,
)

__all__ = [
    "TTSProvider",
    "VoiceProvider",
    "get_voice_engine",
    "active_provider",
    "VoiceModel",
    "NeuralTTS",
    "VoiceCloner",
    "ProsodyEngine",
    "EmotionVoice",
    "StreamingVoice",
    "RealtimeTTS",
    "LipSyncEngine",
    "humanize_text",
    "apply_human_prosody",
    "delivery_plan",
    "VoiceProfile",
    "VoiceProfiles",
    "OMVoiceProfile",
    "jarvis_butler_profile",
]
