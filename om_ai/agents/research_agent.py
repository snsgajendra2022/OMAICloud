"""
Research Agent
"""


import re

from .base import BaseAgent



class ResearchAgent(BaseAgent):


    name="research"



    def can_handle(
        self,
        question
    ):


        if re.search(
            r"\b(research|study|paper|explain|why|history)\b",
            question,
            re.I
        ):

            return 0.8


        return 0.0



    def execute(
        self,
        question,
        context=None
    ):


        return {


            "agent":

                self.name,


            "strategy":

            "deep_research",


            "retrieval":

            [

                "papers",

                "knowledge_base",

                "verified_sources"

            ],


            "reasoning":

            [

                "collect facts",

                "compare information",

                "summarize findings"

            ]

        }
