from om_ai.agents.allocation import AgentAllocator



allocator = AgentAllocator()



tasks=[

    "Create Laravel REST API",

    "Design database migration",

    "Research payment gateway options",

    "Create security authentication system"

]



for task in tasks:


    result = allocator.allocate(task)


    print("----------------")

    print(task)

    print(result)
