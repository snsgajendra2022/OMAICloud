class CheckpointValidator:



    def validate(
        self,
        benchmark
    ):


        return (

            benchmark["score"]

            >=

            0.75

        )