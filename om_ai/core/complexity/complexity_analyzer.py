from __future__ import annotations


import re



class ComplexityAnalyzer:
    """
    Analyze question complexity.

    Later connected with:
    - embeddings
    - OM reasoning engine
    - classifier models
    """



    def analyze_text(
        self,
        text: str
    ):


        length = len(
            text.split()
        )


        sentences = len(
            re.findall(
                r"[.!?]",
                text
            )
        )


        return {


            "knowledge_depth":

                min(
                    length * 2,
                    100
                ),



            "reasoning_depth":

                min(
                    sentences * 10,
                    100
                ),



            "coding_complexity":

                self.detect_coding(
                    text
                ),



            "abstraction_level":

                self.detect_abstraction(
                    text
                ),



            "dependency_depth":

                min(
                    text.count(
                        "and"
                    )
                    *
                    5,

                    100

                ),



            "architecture_complexity":

                self.detect_architecture(
                    text
                )

        }



    def detect_coding(
        self,
        text
    ):


        words = [

            "code",

            "implement",

            "system",

            "api",

            "database",

            "algorithm"

        ]


        score = sum(

            10

            for word in words

            if word in text.lower()

        )


        return min(
            score,
            100
        )



    def detect_abstraction(
        self,
        text
    ):


        words = [

            "architecture",

            "design",

            "strategy",

            "framework",

            "concept"

        ]


        return min(

            sum(

                15

                for word in words

                if word in text.lower()

            ),

            100

        )



    def detect_architecture(
        self,
        text
    ):


        words = [

            "distributed",

            "scalable",

            "production",

            "microservice",

            "system"

        ]


        return min(

            sum(

                20

                for word in words

                if word in text.lower()

            ),

            100

        )