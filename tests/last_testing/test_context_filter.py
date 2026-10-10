from om_ai.knowledge.context_filter import KnowledgeContextFilter


filter = KnowledgeContextFilter()


knowledge = [

"Git is a distributed version control system used by developers.",

"India Prime Minister is head of government.",

"Industrial Revolution steam engine physics mechanics."

]


result = filter.filter_hits(
    "what is git",
    knowledge
)


for item in result:
    print(item)