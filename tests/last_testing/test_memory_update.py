from om_ai.memory import MemoryManager


memory = MemoryManager()


memory.remember_conversation(
    "My project is OM AI Operating Brain",
    "ok"
)


print(
    memory.get_context()
)