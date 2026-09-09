from .research_planner import ResearchPlanner
from .rag_engine import RAGEngine


class ResearchEngine:



    def __init__(
        self,
        store
    ):

        self.planner=ResearchPlanner()

        self.rag=RAGEngine(
            store
        )



    def research(
        self,
        question
    ):


        plan = (
            self.planner.create(
                question
            )
        )


        knowledge = (
            self.rag.retrieve(
                question
            )
        )


        return {

            "question":
                question,

            "plan":
                plan,

            "knowledge":
                knowledge

        }