class SemanticParser:


    def parse(self, text: str):

        return {

            "original_text": text,

            "length": len(text),

            "words": text.lower().split(),

            "question":
                self.is_question(text),

            "contains_action":
                self.contains_action(text)

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