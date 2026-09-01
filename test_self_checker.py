from om_ai.evaluation.self_checker import SelfEvaluator


checker = SelfEvaluator()


tests = [

    {
        "question":
        "create react native login screen",

        "answer":
        """
        Create React Native Login Screen.
        Includes UI components,
        validation and navigation.
        """,

        "technology":
        {
            "technology":
            "react native"
        }

    },


    {
        "question":
        "create react native login screen",

        "answer":
        """
        Create HTML CSS webpage.
        """,

        "technology":
        {
            "technology":
            "react native"
        }

    }

]


for item in tests:

    print("\nRESULT")

    print(
        checker.evaluate(
            item["question"],
            item["answer"],
            item["technology"]
        )
    )