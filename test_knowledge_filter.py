from om_ai.knowledge.context_filter import KnowledgeContextFilter


filter_engine = KnowledgeContextFilter()


tests = [

    {
        "query":
        "create react native login screen",

        "knowledge":
        {
            "answer":
            """
            React Native uses JavaScript
            to create mobile applications.
            """
            ,
            "domain":
            "programming"
        },

        "technology":
        {
            "technology":
            "react native"
        },

        "intent":
        {
            "domain":
            "programming"
        }
    },


    {
        "query":
        "create react native login screen",

        "knowledge":
        {
            "answer":
            """
            Industrial Revolution steam engines
            and Maxwell electromagnetism.
            """,

            "domain":
            "history"
        },

        "technology":
        {
            "technology":
            "react native"
        },

        "intent":
        {
            "domain":
            "programming"
        }
    }

]


for item in tests:


    result = filter_engine.filter(
        item["query"],
        item["knowledge"],
        item["intent"],
        item["technology"]
    )


    print("\nRESULT")
    print(result)