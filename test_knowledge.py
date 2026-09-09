from om_ai.core.knowledge_intelligence import *


store = KnowledgeStore()


store.add(

KnowledgeItem(

title="React",

content=
"React is a JavaScript frontend library",

category="software",

confidence=0.95

)

)


engine = ResearchEngine(
    store
)


result = engine.research(
    "What is React?"
)


print(result)