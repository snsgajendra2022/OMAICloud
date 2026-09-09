class ProblemAnalyzer:


    def analyze(self, user_input, message=None):

        text = (user_input or message or "").strip()
        msg = (message or user_input or "").strip()

        return {

            "input":
                text,

            "goal":
                self.detect_goal(text),

            "complexity":
                self.detect_complexity(text),

            "problem":
                msg,

            "type":
                self.detect_type(msg),

        }


    def detect_goal(self, text):

        text = (text or "").lower()

        if "create" in text or "build" in text:
            return "creation"

        if "code" in text or "react" in text:
            return "software"

        if "why" in text:
            return "explanation"

        if "fix" in text or "error" in text:
            return "debugging"

        return "general"


    def detect_complexity(self, text):

        words = len((text or "").split())
        if words > 50:
            return "complex"
        return "normal"


    def detect_type(self, text):

        text = (text or "").lower()
        if any(k in text for k in ("code", "react", "python", "api", "function", "app")):
            return "coding"
        if any(k in text for k in ("why", "explain", "what is")):
            return "explanation"
        if any(k in text for k in ("hi", "hello", "hey", "thanks")):
            return "conversation"
        return "general"
