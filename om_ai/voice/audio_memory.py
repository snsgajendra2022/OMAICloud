"""
OM Voice Interaction Memory
"""


from pathlib import Path

import json



class VoiceMemory:


    def __init__(self):


        self.path=Path(

            "data/om-memory/voice_history.json"

        )


        self.path.parent.mkdir(

            parents=True,

            exist_ok=True

        )


        if not self.path.exists():

            self.path.write_text(

                "[]"

            )



    def store(

        self,

        data

    ):


        history=json.loads(

            self.path.read_text()

        )


        history.append(

            data

        )


        self.path.write_text(

            json.dumps(

                history,

                indent=2

            )

        )



    def all(self):


        return json.loads(

            self.path.read_text()

        )