from concurrent.futures import ThreadPoolExecutor

from om_ai.memory.conversations import ConversationStore


def test_project_chat_listing_is_safe_while_conversations_are_created(tmp_path):
    store = ConversationStore(str(tmp_path / "conversations.sqlite3"))
    tenant_id = "tenant-a"
    actor = "user:alice"

    def exercise(index: int) -> int:
        conversation = store.create_conversation(
            tenant_id, actor, title=f"Chat {index}"
        )
        store.append_messages(
            conversation.id,
            tenant_id,
            actor,
            [
                {"role": "user", "content": f"Question {index}"},
                {"role": "assistant", "content": f"Answer {index}"},
            ],
        )
        # Mirrors the project chats endpoint's filtered query and parameter binding.
        return len(store.list_conversations(
            tenant_id, actor, project_id="project-a"
        ))

    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(exercise, range(40)))

        assert results == [0] * 40
        conversations = store.list_conversations(tenant_id, actor)
        assert len(conversations) == 40
        assert sum(item.message_count for item in conversations) == 80
    finally:
        store.close()
