from .intent_classifier import ResponseIntentClassifier
from .response_strategy import ResponseStrategy
from .answer_planner import AnswerPlanner
from .format_selector import FormatSelector
from .quality_checker import QualityChecker
from .improvement_engine import ImprovementEngine



class ResponseEngine:


    def __init__(self):

        self.intent = ResponseIntentClassifier()

        self.strategy =  ResponseStrategy()

        self.planner =  AnswerPlanner()

        self.format = FormatSelector()

        self.checker = QualityChecker()

        self.improver = ImprovementEngine()



    def prepare(self, user_input):


        intent = self.intent.classify(
            user_input
        )


        strategy = self.strategy.select(
            intent
        )


        plan = self.planner.create(
            strategy
        )


        return {

            "intent":intent,

            "strategy":strategy,

            "plan":plan,

            "format":
                self.format.select(strategy)

        }


    def finalize(self,response):


        improved = self.improver.improve(
            response
        )


        return self.checker.check(
            improved
        )