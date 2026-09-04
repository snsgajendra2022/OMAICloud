class ResponseStrategy:


    def select(self, intent):


        strategies = {

            "implementation":
                "code_first",

            "explanation":
                "teaching",

            "planning":
                "architecture",

            "general":
                "conversation"

        }


        return strategies.get(
            intent,
            "conversation"
        )