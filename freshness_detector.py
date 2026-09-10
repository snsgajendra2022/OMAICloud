class FreshnessDetector:


    def needs_web(self, question):

        signals = [

            "latest",
            "today",
            "current",
            "new",
            "recent",
            "price",
            "release"

        ]


        question = question.lower()


        for signal in signals:

            if signal in question:
                return True


        return False