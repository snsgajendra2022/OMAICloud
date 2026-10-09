from om_ai.knowledge.ranker import KnowledgeRanker


ranker = KnowledgeRanker()


documents = [

    {
        "text": """
        Git is a distributed version control system.
        Developers use Git to manage source code.
        """,
        "domain": "programming",
        "source": "official",
        "quality_score": 0.95
    },


    {
        "text": """
        The Prime Minister of India is the head of government.
        """,
        "domain": "civics",
        "source": "wikipedia",
        "quality_score": 0.90
    },


    {
        "text": """
        React is a JavaScript library for building interfaces.
        """,
        "domain": "programming",
        "source": "documentation",
        "quality_score": 0.90
    }

]


result = ranker.rank(

    "what is git",

    documents,

    intent={
        "domain": "programming"
    },

    technology={
        "technology": "git"
    }

)


print("\n===== RANK RESULT =====")


for item in result:

    print("\nScore:", item.score)

    print("Confidence:", item.confidence)

    print("Domain:", item.domain)

    print("Reasons:", item.reasons)

    print("Text:", item.text[:100])