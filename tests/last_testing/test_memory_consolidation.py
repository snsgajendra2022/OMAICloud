



from om_ai.memory_intelligence.consolidator import MemoryConsolidator


engine = MemoryConsolidator()



result = engine.consolidate(

    {

        "type":"project",

        "content":{

            "project":

            "Restaurant Management System",

            "technology":

            "Laravel",

            "decision":

            "Multi tenant architecture"

        }

    }

)



print(result)