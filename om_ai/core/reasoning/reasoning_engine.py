from .problem_analyzer import ProblemAnalyzer
from .planner import Planner
from .chain_reasoner import ChainReasoner
from .critic import Critic
from .verifier import Verifier



class ReasoningEngine:


    def __init__(self):

        self.analyzer=ProblemAnalyzer()

        self.planner=Planner()

        self.reasoner=ChainReasoner()

        self.critic=Critic()

        self.verifier=Verifier()



    def process(self,user_input):


        analysis = self.analyzer.analyze(
            user_input
        )


        plan = self.planner.create_plan(
            analysis
        )


        reasoning = self.reasoner.reason(
            analysis,
            plan
        )


        return reasoning