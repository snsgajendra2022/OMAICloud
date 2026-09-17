class AIMetrics:


    def __init__(self):

        self.data={}



    def increase(
        self,
        name
    ):

        self.data[name]=(
            self.data.get(name,0)+1
        )



    def get(
        self
    ):

        return self.data