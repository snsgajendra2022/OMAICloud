from om_ai.conversation_engine import ConversationEngine
def test_contextual_reference_and_task():
    r=ConversationEngine().process("fix that",history=[{"role":"user","content":"React white screen error"},{"role":"assistant","content":"Check the console."}],tenant_id="t",actor="u")
    assert r["relation"]["relation"]=="reference_to_past";assert r["state"].active_task
def test_contextual_confirmation():
    r=ConversationEngine().process("yes",history=[{"role":"assistant","content":"Should I fix ModelGateway first?"}],tenant_id="t2",actor="u")
    assert r["relation"]["relation"]=="confirmation"
def test_topic_switch():
    r=ConversationEngine().process("Now help me with SQL indexes.",history=[{"role":"user","content":"Help me fix React white screen."}],tenant_id="t3",actor="u")
    assert r["state"].current_topic=="sql"
