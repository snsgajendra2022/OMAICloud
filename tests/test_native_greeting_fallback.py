from om_ai.runtime.engine import deterministic_greeting_reply


def test_simple_hello_gets_reliable_reply():
    assert deterministic_greeting_reply([{"role": "user", "content": "hello"}]) == (
        "Hello! How can I help you today?"
    )


def test_common_typo_helo_gets_reliable_reply():
    assert deterministic_greeting_reply([{"role": "user", "content": "helo!"}]) == (
        "Hello! How can I help you today?"
    )


def test_greeting_with_question_is_not_intercepted():
    assert deterministic_greeting_reply(
        [{"role": "user", "content": "hello, can you explain Python lists?"}]
    ) is None


def test_non_user_last_message_is_not_intercepted():
    assert deterministic_greeting_reply(
        [{"role": "assistant", "content": "hello"}]
    ) is None
