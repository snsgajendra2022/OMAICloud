"""
OM Dataset Version Manager
"""


from pathlib import Path

import json

from datetime import datetime





class DatasetVersionManager:



    def __init__(

        self,

        path="data/om-training/versions"

    ):


        self.path=Path(path)


        self.path.mkdir(

            parents=True,

            exist_ok=True

        )




    def save(

        self,

        dataset:list[dict]

    ):


        version = datetime.utcnow().strftime(

            "%Y%m%d_%H%M%S"

        )


        file=self.path / (

            f"dataset_{version}.json"

        )


        file.write_text(

            json.dumps(

                dataset,

                indent=2

            )

        )


        return str(file)