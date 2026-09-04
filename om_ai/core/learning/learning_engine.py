from .experience_collector import ExperienceCollector

from .evaluator import LearningEvaluator

from .improvement_analyzer import ImprovementAnalyzer

from .knowledge_updater import KnowledgeUpdater



class LearningEngine:


    def __init__(self):

        self.collector = ExperienceCollector()

        self.evaluator = LearningEvaluator()

        self.analyzer = ImprovementAnalyzer()

        self.updater = KnowledgeUpdater()



    def learn(
        self,
        input_text,
        response
    ):


        experience = self.collector.collect(
            input_text,
            response
        )


        evaluation = self.evaluator.evaluate(
            experience
        )


        improvement = self.analyzer.analyze(
            evaluation
        )


        update = self.updater.update(
            improvement
        )


        return {

            "experience":
                experience,

            "evaluation":
                evaluation,

            "improvement":
                improvement,

            "update":
                update

        }