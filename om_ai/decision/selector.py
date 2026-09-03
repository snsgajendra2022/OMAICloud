"""
OM Best Decision Selector
"""




class DecisionSelector:



    def select(

        self,

        options:list,

        scores:dict

    ):


        best=max(

            options,

            key=lambda x:

            scores.get(

                x.name,

                0

            )

        )



        return best