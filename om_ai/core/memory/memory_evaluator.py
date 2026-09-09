class MemoryEvaluator:


    def should_store(
        self,
        experience
    ):


        important_words=[

            "prefer",

            "always",

            "my project",

            "I use",

            "I like",

            "remember"

        ]


        text = (
            experience["content"]
            .lower()
        )


        for word in important_words:


            if word in text:

                return True


        return False