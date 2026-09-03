"""
OM Context Merger

Combines RAG + Graph knowledge.
"""





class ContextMerger:



    def merge(

        self,

        vector_hits:list,

        graph_hits:list

    ):


        context=[]



        for item in vector_hits:


            if isinstance(item,dict):

                context.append(

                    item.get(
                        "text",
                        ""

                    )

                )

            else:

                context.append(

                    str(item)

                )



        for relation in graph_hits:


            context.append(

                (

                    relation.get("source")

                    +

                    " "

                    +

                    relation.get("relation")

                    +

                    " "

                    +

                    relation.get("target")

                )

            )



        return list(

            dict.fromkeys(

                context

            )

        )