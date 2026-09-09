class SemanticParser:

    def parse(
        self,
        message
    ):

        text = message.original_text

        return {
            "text": text,

            "sentences":
                message.sentences,

            "word_count":
                message.word_count,

            "character_count":
                message.character_count,

            "question":
                self._is_question(text),

            "request":
                self._is_request(text)
        }

    def is_question(self, text):

        return "?" in text



    def contains_action(self, text):

        actions = [

            "create",
            "build",
            "make",
            "generate",
            "fix",
            "update"

        ]

        text=text.lower()

        return any(
            action in text
            for action in actions
        )


 

    def _is_question(
        self,
        text: str
    ) -> bool:

        return (
            "?" in text
            or
            any(
                text.lower().startswith(x)
                for x in [
                    "what ",
                    "why ",
                    "how ",
                    "when ",
                    "where ",
                    "who ",
                    "which ",
                    "can ",
                    "could ",
                    "would ",
                    "is "
                ]
            )
        )


    def _is_request(
        self,
        text: str
    ) -> bool:

        return any(
            text.lower().startswith(x)
            for x in [
                "please ",
                "can you ",
                "could you ",
                "i want ",
                "i need ",
                "create ",
                "make ",
                "build "
            ]
        )