from om_ai.knowledge.retrieval import HybridRetriever


engine = HybridRetriever()


results = engine.search(
    "what is git",
    k=5
)


for item in results:

    print("----------------")

    print(item["text"])

    print(
        "Score:",
        item.get("hybrid_score")
    )