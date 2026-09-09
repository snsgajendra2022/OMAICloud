from .answer_planner import AnswerPlanner
from .format_selector import FormatSelector
from .quality_checker import QualityChecker


class ResponseEngine:


    def __init__(self):

        self.planner = AnswerPlanner()

        self.formatter = FormatSelector()

        self.checker = QualityChecker()



    def prepare(
        self,
        message,
        intent
    ):


        plan = self.planner.plan(
            intent,
            message
        )


        response_type = (
            self.formatter.select(
                message,
                intent
            )
        )


        return {

            "plan":plan,

            "response_type":
                response_type

        }



    def validate(
        self,
        response
    ):

        return self.checker.validate(
            response
        )