"""
OM Speech Recognition Layer

Future integrations:

- Whisper
- Vosk
- DeepSpeech
"""


class SpeechToText:


    def transcribe(
        self,
        audio
    ):


        return {


            "text":
                str(audio),


            "confidence":
                0.0,


            "language":
                "unknown"

        }