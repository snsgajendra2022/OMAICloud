from .problem_analyzer import ProblemAnalyzer
from .decomposition_engine import DecompositionEngine
from .planning_engine import PlanningEngine
from .verification_engine import VerificationEngine
from .reasoning_memory import ReasoningMemory



class ReasoningEngine:


    def __init__(self):

        self.analyzer=ProblemAnalyzer()

        self.decomposer=DecompositionEngine()

        self.planner=PlanningEngine()

        self.verifier=VerificationEngine()

        self.memory=ReasoningMemory()



    def reason(
        self,
        problem
    ):


        analysis=self.analyzer.analyze(
            problem
        )


        steps=self.decomposer.split(
            problem
        )


        plan=self.planner.create_plan(
            steps
        )


        result={

            "problem":
                problem,


            "analysis":
                analysis,


            "plan":
                plan

        }


        self.memory.store(
            result
        )


        return result



    def verify(
        self,
        answer
    ):

        return self.verifier.verify(
            answer
        )