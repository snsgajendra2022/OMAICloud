class ContextAnalyzer:


    def analyze(
        self,
        semantic,
        previous_context=None
    ):


        return {

            "is_question":
                semantic["question"],


            "previous":
                previous_context or {},


            "conversation_type":
                self.detect_type(
                    semantic["original_text"]
                )

        }



    def detect_type(self,text):

        text=text.lower()


        if any(
            x in text
            for x in [
                "good morning",
                "hello",
                "hi",
                "hey"
            ]
        ):

            return "conversation"


        return "information"