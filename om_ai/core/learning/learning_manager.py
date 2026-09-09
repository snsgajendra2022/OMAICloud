from .experience_collector import ExperienceCollector
from .learning_analyzer import LearningAnalyzer
from .failure_detector import FailureDetector
from .improvement_engine import ImprovementEngine
from .behavior_optimizer import BehaviorOptimizer



class LearningManager:



    def __init__(self):

        self.collector = (
            ExperienceCollector()
        )

        self.analyzer = (
            LearningAnalyzer()
        )

        self.failure = (
            FailureDetector()
        )

        self.improver = (
            ImprovementEngine()
        )

        self.optimizer = (
            BehaviorOptimizer()
        )



    def learn(
        self,
        message,
        response
    ):


        experience = (
            self.collector.collect(
                message,
                response
            )
        )


        experience = (
            self.analyzer.analyze(
                experience
            )
        )


        problems = (
            self.failure.detect(
                experience
            )
        )


        improvements = (
            self.improver.improve(
                problems
            )
        )


        behavior = (
            self.optimizer.update(
                improvements
            )
        )


        return {

            "experience":
                experience,

            "problems":
                problems,

            "improvements":
                improvements,

            "behavior":
                behavior

        }