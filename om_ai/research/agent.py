"""
OM Research Intelligence Agent
"""


from .planner import ResearchPlanner

from .collector import InformationCollector

from . analyzer import ResearchAnalyzer

from .validator import FactValidator

from .summarizer import ResearchSummarizer

from .memory import ResearchMemory



class ResearchAgent:


    def __init__(self):


        self.planner = ResearchPlanner()

        self.collector = InformationCollector()

        self.analyzer = ResearchAnalyzer()

        self.validator = FactValidator()

        self.summarizer = ResearchSummarizer()

        self.memory = ResearchMemory()



    def research(

        self,

        question,

        knowledge=None

    ):


        plan=self.planner.create_plan(

            question

        )


        collected=self.collector.collect(

            question,

            knowledge

        )


        analysis=self.analyzer.analyze(

            collected

        )


        validation=self.validator.validate(

            analysis

        )


        summary=self.summarizer.summarize(

            analysis,

            validation

        )


        result={


            "plan":

                plan,


            "analysis":

                analysis,


            "validation":

                validation,


            "result":

                summary

        }


        self.memory.store(

            result

        )


        return result