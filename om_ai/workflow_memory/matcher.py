"""
OM Workflow Similarity Matcher
"""




class StrategyMatcher:



    def match(

        self,

        goal,

        memories

    ):


        goal_words=set(

            goal.lower().split()

        )


        results=[]



        for memory in memories:


            memory_goal=set(

                memory["goal"]

                .lower()

                .split()

            )



            similarity=len(

                goal_words & memory_goal

            ) / max(

                len(goal_words),

                1

            )



            results.append(

                {

                    "memory":

                        memory,

                    "similarity":

                        round(

                            similarity,

                            2

                        )

                }

            )



        results.sort(

            key=lambda x:

            x["similarity"],

            reverse=True

        )



        return results