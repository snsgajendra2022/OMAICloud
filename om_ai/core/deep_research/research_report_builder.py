class ResearchReportBuilder:



    def build(
        self,
        query,
        evidence
    ):


        return {


            "query":

                query,


            "evidence":

                evidence,


            "confidence":

                self.calculate_confidence(
                    evidence
                )

        }



    def calculate_confidence(
        self,
        evidence
    ):


        if not evidence:

            return 0


        return round(

            sum(
                e.confidence
                for e in evidence
            )
            /
            len(evidence),

            2

        )