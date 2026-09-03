"""
OM Training Experience Collector

Collects:
- Agent results
- Workflow results
- Research results
- Failure recovery
"""


from datetime import datetime



class ExperienceCollector:


    def create(

        self,

        input_text,

        output_text,

        metadata=None

    ):


        return {


            "input":

                input_text,


            "output":

                output_text,


            "metadata":

                metadata or {},


            "created_at":

                datetime.utcnow().isoformat()

        }