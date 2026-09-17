class CollaborationEngine:


    def collaborate(
        self,
        results
    ):


        return {

            "agents":

                [

                    r.agent

                    for r in results

                ],


            "outputs":

                [

                    r.output

                    for r in results

                ]

        }