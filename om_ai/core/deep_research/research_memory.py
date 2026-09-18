class ResearchMemory:


    def __init__(self):

        self.records=[]



    def store(
        self,
        report
    ):

        self.records.append(
            report
        )



    def search(
        self,
        query
    ):


        return [

            x for x in self.records

            if query.lower()
            in str(x).lower()

        ]