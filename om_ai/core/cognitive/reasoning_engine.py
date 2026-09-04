class ReasoningEngine:


    def analyze(self, context):

        return {

            "problem":
                context.get("input"),

            "reasoning_steps":[

                "understand_problem",

                "collect_context",

                "generate_solution",

                "verify_solution"

            ]

        }


    def execute(self, reasoning):

        return {

            "reasoning":
                reasoning,

            "status":
                "completed"

        }