"""
OM Autonomous QA Agent
"""


from .generator import TestGenerator

from .runner import TestRunner

from .analyzer import QualityAnalyzer

from .quality import QualityScore

from .memory import TestingMemory





class TestingAgent:



    def __init__(self):


        self.generator=TestGenerator()

        self.runner=TestRunner()

        self.analyzer=QualityAnalyzer()

        self.score=QualityScore()

        self.memory=TestingMemory()




    def evaluate(

        self,

        requirement,

        code=""

    ):


        tests=self.generator.generate(

            requirement

        )


        results=self.runner.run(

            tests

        )


        analysis=self.analyzer.analyze(

            code

        )


        quality=self.score.calculate(

            results,

            analysis

        )


        report={


            "requirement":

                requirement,


            "tests":

                results,


            "analysis":

                analysis,


            "quality_score":

                quality

        }



        self.memory.store(

            report

        )


        return report