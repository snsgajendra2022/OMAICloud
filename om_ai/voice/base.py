from __future__ import annotations
from abc import ABC, abstractmethod

class SpeechToTextBackend(ABC):
    @abstractmethod
    def transcribe(self,audio_path:str)->str: ...

class TextToSpeechBackend(ABC):
    @abstractmethod
    def synthesize(self,text:str,output_path:str)->str: ...

class NullSpeechBackend(SpeechToTextBackend, TextToSpeechBackend):
    def transcribe(self,audio_path:str)->str:
        raise RuntimeError('No local speech-to-text model configured')
    def synthesize(self,text:str,output_path:str)->str:
        raise RuntimeError('No local text-to-speech model configured')
