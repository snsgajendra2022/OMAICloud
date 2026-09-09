class ContextAnalyzer:


    def analyze(
        self,
        semantic,
        previous_context=None,
        conversation=None,
        current_message=None,
    ):


        return {

            "is_question":
                semantic["question"],


            "previous":
                previous_context or {},


            "conversation_type":
                self.detect_type(
                    semantic["original_text"]
                ),
                  "current_message":
                current_message.original_text,

            "previous_messages":
                conversation,

            "conversation_length":
                len(conversation)

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


  