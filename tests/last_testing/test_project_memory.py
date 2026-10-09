from om_ai.memory import MemoryManager


memory=MemoryManager()


memory.remember_project(

    "restaurant",

    "Restaurant Management System uses Laravel 9 and MySQL"

)



print(

memory.get_relevant_memory(

    "tell me restaurant technology"

)

)