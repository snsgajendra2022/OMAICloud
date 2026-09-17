class EvidenceValidator:


    def validate(
        self,
        evidence
    ):


        return {

            "valid":
                bool(evidence.content),

            "confidence":
                evidence.confidence

        }