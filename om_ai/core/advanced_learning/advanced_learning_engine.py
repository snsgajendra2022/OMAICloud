from .pattern_learner import PatternLearner
from .knowledge_builder import KnowledgeBuilder
from .dataset_generator import DatasetGenerator
from .evaluation_engine import EvaluationEngine
from .improvement_planner import ImprovementPlanner



class AdvancedLearningEngine:



    def __init__(self):

        self.patterns = PatternLearner()

        self.knowledge = KnowledgeBuilder()

        self.dataset = DatasetGenerator()

        self.evaluator = EvaluationEngine()

        self.planner = ImprovementPlanner()



    def learn(
        self,
        records
    ):


        patterns = (
            self.patterns.learn(
                records
            )
        )


        knowledge = (
            self.knowledge.build(
                patterns
            )
        )


        dataset = (
            self.dataset.generate(
                records
            )
        )


        return {

            "patterns":
                patterns,


            "knowledge":
                knowledge,


            "dataset":
                dataset

        }



    def improve(
        self,
        response
    ):


        evaluation = (
            self.evaluator.evaluate(
                response
            )
        )


        improvements = (
            self.planner.plan(
                evaluation
            )
        )


        return {

            "evaluation":
                evaluation,


            "improvements":
                improvements

        }