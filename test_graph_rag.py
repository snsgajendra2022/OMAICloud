from om_ai.knowledge.graph_rag import GraphRAGExpander



engine = GraphRAGExpander()



vector=[

    {

        "text":

        "Laravel is a PHP framework"

    }

]



result = engine.expand(

    "Laravel API",

    vector

)



for item in result:

    print("----------------")

    print(item)