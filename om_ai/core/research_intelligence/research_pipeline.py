from .research_engine import ResearchEngine



class ResearchPipeline:


    def __init__(self):

        self.engine = ResearchEngine()



    def run(
        self,
        query
    ):


        task = (
            self.engine.create(
                query
            )
        )


        return {

            "research_required":
                True,

            "task":
                task

        }