from om_ai.core.memory import MemoryManager

memory = MemoryManager()

memory.process(
    "I use React and I prefer TypeScript"
)


memory.process(
    "My main project is OM AI"
)



results = memory.recall(
    "React"
)


for item in results:

    print(
        item.content
    )