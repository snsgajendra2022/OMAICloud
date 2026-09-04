class FormatSelector:


    def select(self, strategy):


        if strategy=="code_first":

            return "markdown_code"


        if strategy=="architecture":

            return "structured"


        return "normal"