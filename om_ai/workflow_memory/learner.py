"""
OM Autonomous Workflow Learning Engine
"""


from pathlib import Path

import json



from .extractor import WorkflowExtractor





class WorkflowLearningEngine:



    def __init__(self):


        self.extractor = WorkflowExtractor()


        self.path = Path(

            "data/om-memory/workflow_strategy.json"

        )


        self.path.parent.mkdir(

            parents=True,

            exist_ok=True

        )


        if not self.path.exists():

            self.path.write_text(

                "[]"

            )




    def learn(

        self,

        workflow,

        success=True,

        score=1.0

    ):


        data=json.loads(

            self.path.read_text()

        )


        extracted=self.extractor.extract(

            workflow

        )


        record={


            "goal":

                workflow.get(

                    "goal",

                    ""

                ),


            "pattern":

                extracted["pattern"],


            "success":

                success,


            "score":

                score

        }



        data.append(

            record

        )



        self.path.write_text(

            json.dumps(

                data,

                indent=2

            )

        )


        return record




    def all(self):


        return json.loads(

            self.path.read_text()

        )