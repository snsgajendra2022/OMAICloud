class ProblemAnalyzer:


    def analyze(self, user_input):

        return {

            "input":
                user_input,

            "goal":
                self.detect_goal(user_input),

            "complexity":
                self.detect_complexity(user_input)

        }


    def detect_goal(self,text):

        text=text.lower()


        if "create" in text or "build" in text:

            return "creation"


        if "why" in text:

            return "explanation"


        if "fix" in text or "error" in text:

            return "debugging"


        return "general"



    def detect_complexity(self,text):

        words=len(text.split())


        if words > 50:

            return "complex"


        return "normal"