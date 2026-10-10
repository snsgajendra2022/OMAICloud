from om_ai.core.chat_intelligence.intent_understanding import IntentUnderstanding


def test_hinglish_explanation_routes_to_explanation():
    result = IntentUnderstanding().understand(
        "Mujhe simple English mein batao ki Python list kya hoti hai."
    )
    assert result.intent == "explain"
    assert result.needs_model is True


def test_hinglish_how_to_routes_to_steps():
    result = IntentUnderstanding().understand(
        "React app kaise banaye?"
    )
    assert result.intent == "coding"
    assert result.strategy == "code_solution"


def test_hinglish_followup_is_recognized_with_history():
    result = IntentUnderstanding().understand(
        "Aur iske baare mein batao",
        history=[{"role": "user", "content": "Explain Python lists"}],
    )
    assert result.intent in {"howto", "followup", "explain"}
