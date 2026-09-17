class ResearchAgent:


    name="research_agent"



    def create_task(
        self,
        query
    ):


        return {

            "query":query,

            "status":
                "created"

        }