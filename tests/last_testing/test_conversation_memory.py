from om_ai.memory.conversation import ConversationMemory


memory = ConversationMemory()


memory.add_user_message(
    "Create React Native application"
)


memory.add_assistant_message(
    "I will create mobile architecture"
)


memory.add_user_message(
    "Add login screen"
)


print(
    memory.get_messages()
)


print("\nCONTEXT\n")

print(
    memory.get_context()
)