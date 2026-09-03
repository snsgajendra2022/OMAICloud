"""
OM Safety Audit System
"""


from pathlib import Path

import json

from datetime import datetime





class SafetyAudit:



    def __init__(self):


        self.path=Path(

            "data/om-memory/safety_audit.json"

        )


        self.path.parent.mkdir(

            parents=True,

            exist_ok=True

        )


        if not self.path.exists():

            self.path.write_text(

                "[]"

            )




    def record(

        self,

        data

    ):


        logs=json.loads(

            self.path.read_text()

        )


        data["time"]=datetime.utcnow().isoformat()


        logs.append(

            data

        )


        self.path.write_text(

            json.dumps(

                logs,

                indent=2

            )

        )