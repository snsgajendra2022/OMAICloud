"""Voice modality package (weights external)."""
from om_ai.voice.base import NullSpeechBackend, SpeechToTextBackend, TextToSpeechBackend

__all__ = ["SpeechToTextBackend", "TextToSpeechBackend", "NullSpeechBackend"]
