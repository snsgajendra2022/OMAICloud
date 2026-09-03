"""
OM Voice Intelligence Agent
"""


from .speech_to_text import SpeechToText

from .text_to_speech import TextToSpeech

from .voice_command import VoiceCommandAnalyzer

from .audio_memory import VoiceMemory





class VoiceAgent:


    def __init__(self):


        self.stt=SpeechToText()

        self.tts=TextToSpeech()

        self.command=VoiceCommandAnalyzer()

        self.memory=VoiceMemory()



    def process(

        self,

        audio

    ):


        text=self.stt.transcribe(

            audio

        )


        command=self.command.analyze(

            text["text"]

        )


        response={


            "input":

                text,


            "command":

                command

        }


        self.memory.store(

            response

        )


        return response