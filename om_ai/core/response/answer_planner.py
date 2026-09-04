class AnswerPlanner:


    def create(self, strategy):


        if strategy=="code_first":

            return [

                "Understand requirement",

                "Select technology",

                "Generate implementation",

                "Explain usage"

            ]


        if strategy=="architecture":

            return [

                "Analyze system",

                "Explain components",

                "Show architecture",

                "Explain tradeoffs"

            ]


        return [

            "Understand",

            "Answer"

        ]