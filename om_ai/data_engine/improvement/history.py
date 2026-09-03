"""
OM Improvement History Storage
"""


from pathlib import Path

import json





class ImprovementHistory:



    def __init__(
        self,
        path="data/om-training/improvements.json"
    ):


        self.path = Path(path)


        self.path.parent.mkdir(

            parents=True,

            exist_ok=True

        )



    def save(
        self,
        item
    ):


        data=[]


        if self.path.exists():

            data=json.loads(

                self.path.read_text()

            )



        data.append(item)



        self.path.write_text(

            json.dumps(

                data,

                indent=2

            )

        )


        return True