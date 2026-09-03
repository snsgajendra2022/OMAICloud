"""
OM Speech Generation Layer

Future:

- Coqui TTS
- Piper
- ElevenLabs
"""


class TextToSpeech:


    def generate(

        self,

        text

    ):


        return {


            "text":
                text,


            "audio":
                None,


            "status":
                "ready"

        }