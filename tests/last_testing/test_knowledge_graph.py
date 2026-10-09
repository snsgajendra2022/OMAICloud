from om_ai.knowledge_graph import KnowledgeGraphEngine



engine = KnowledgeGraphEngine()



result = engine.learn(

    "Laravel uses PHP framework with MySQL database and REST API"

)



print(result)



search = engine.search(

    "laravel"

)


print(search)