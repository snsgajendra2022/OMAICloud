class BehaviorOptimizer:



    def __init__(self):

        self.behaviors={}



    def update(
        self,
        improvements
    ):


        for item in improvements:

            self.behaviors[item]=(
                self.behaviors.get(
                    item,
                    0
                )
                +1
            )


        return self.behaviors