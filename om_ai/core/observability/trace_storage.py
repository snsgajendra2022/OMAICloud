import json
from pathlib import Path



class TraceStorage:


    def __init__(
        self,
        path="data/traces.jsonl"
    ):

        self.path=Path(path)

        self.path.parent.mkdir(
            exist_ok=True,
            parents=True
        )



    def save(
        self,
        event
    ):


        with self.path.open(
            "a",
            encoding="utf-8"
        ) as f:

            f.write(
                json.dumps(
                    event.__dict__,
                    default=str
                )
                +
                "\n"
            )



    def read_all(self):

        if not self.path.exists():

            return []


        return [

            json.loads(x)

            for x in self.path.read_text()
            .splitlines()

        ]