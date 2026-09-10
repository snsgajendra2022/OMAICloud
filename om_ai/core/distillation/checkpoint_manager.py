from __future__ import annotations


from pathlib import Path

import json

from datetime import datetime



class CheckpointManager:


    def __init__(
        self,
        path="data/distillation/checkpoints"
    ):


        self.path = Path(path)


        self.path.mkdir(

            parents=True,

            exist_ok=True

        )



    def save(
        self,
        run_id,
        data
    ):


        checkpoint = {


            "run_id":
                run_id,


            "saved_at":
                datetime.utcnow()
                .isoformat(),


            "state":
                data

        }



        file = (

            self.path

            /

            f"{run_id}.json"

        )


        with open(
            file,
            "w",
            encoding="utf-8"
        ) as f:


            json.dump(

                checkpoint,

                f,

                indent=2

            )


        return str(file)



    def load(
        self,
        run_id
    ):


        file = (

            self.path

            /

            f"{run_id}.json"

        )


        if not file.exists():

            return None



        with open(
            file,
            encoding="utf-8"
        ) as f:

            return json.load(f)