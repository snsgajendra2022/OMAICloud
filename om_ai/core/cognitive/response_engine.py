class ResponseEngine:


    def analyze_response_style(
        self,
        context
    ):


        length = len(
            context.get("input","")
        )


        if length < 20:

            return "short"


        elif length < 100:

            return "normal"


        return "detailed"



    def format(
        self,
        answer,
        style
    ):

        return {

            "style":
                style,

            "answer":
                answer

        }