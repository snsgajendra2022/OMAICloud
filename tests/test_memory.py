from om_ai.memory import SQLiteMemoryStore

def test_memory(tmp_path):
    db=SQLiteMemoryStore(str(tmp_path/'m.db'))
    db.add('t','u','likes concise reports','preference')
    assert db.recent('t','u')[0].content=='likes concise reports'
    assert db.search('concise','t','u')
