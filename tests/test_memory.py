from om_ai.memory.short_term import ShortTermMemory

memory = ShortTermMemory()


memory.remember(
    "project",
    "OM AI"
)


memory.remember(
    "stack",
    [
        "Python",
        "FastAPI"
    ]
)


print(
    memory.recall("project")
)


print(
    memory.all()
)