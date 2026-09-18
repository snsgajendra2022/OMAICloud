from __future__ import annotations

import re

from .research_plan import ResearchPlan



class ResearchRouter:
    """
    Decides whether OM needs deep research.

    This is not based only on keywords.
    It evaluates:

    - complexity
    - freshness requirement
    - comparison requirement
    - technical depth
    - uncertainty
    """


    COMPLEX_PATTERNS = [

        r"\barchitecture\b",

        r"\bsystem design\b",

        r"\bdistributed\b",

        r"\bcompare\b",

        r"\bdifference between\b",

        r"\bbest practices\b",

        r"\bhow does .* work\b",

        r"\bdeep dive\b",

        r"\bresearch\b",

        r"\banalyze\b",

        r"\bevaluate\b",

        r"\bproduction\b",

        r"\benterprise\b",

        r"\blatest\b",

        r"\bcurrent\b",

    ]


    def decide(
        self,
        query:str
    ) -> dict:


        text = (
            query
            .strip()
            .lower()
        )


        score = 0


        reasons=[]



        #
        # complexity signals
        #

        for pattern in self.COMPLEX_PATTERNS:


            if re.search(
                pattern,
                text
            ):

                score += 1

                reasons.append(
                    pattern
                )



        #
        # length signal
        #

        words=len(
            text.split()
        )


        if words >= 8:

            score += 1



        #
        # technical domain signal
        #

        technical_terms=[

            "ai",

            "machine learning",

            "software",

            "database",

            "cloud",

            "kubernetes",

            "security",

            "architecture",

            "framework"

        ]


        for term in technical_terms:

            if term in text:

                score += 1

                break



        research_needed = (
            score >= 2
        )



        return {


            "research_needed":
                research_needed,


            "confidence":
                min(
                    score / 5,
                    1.0
                ),


            "complexity_score":
                score,


            "signals":
                reasons,


            "reason":

                "deep_analysis_required"
                if research_needed
                else
                "direct_answer_possible"

        }