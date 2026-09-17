class DecompositionEngine:



    def split(
        self,
        problem
    ):


        sentences = [

            x.strip()

            for x in problem.split(".")
            
            if x.strip()

        ]


        return sentences