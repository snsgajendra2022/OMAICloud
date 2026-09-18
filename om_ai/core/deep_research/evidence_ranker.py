class EvidenceRanker:



    def rank(
        self,
        evidence:list
    ):


        return sorted(

            evidence,

            key=lambda x:
            x.confidence,

            reverse=True

        )