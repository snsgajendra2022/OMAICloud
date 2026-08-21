"""Intelligence layer: memory, language, alignment, instruction following."""
from __future__ import annotations

from om_ai.runtime.intelligence import (
    aligned_memory_reply,
    detect_language,
    enrich_for_chat,
    extract_memory_candidates,
    language_instruction,
)


def test_detect_language_english_and_hindi():
    assert detect_language("Hello how are you") == "en"
    assert detect_language("मेरा नाम गजेंद्र है") == "hi"
    assert detect_language("bhai kya haal hai") == "hi-Latn"


def test_extract_and_align_name_memory():
    cands = extract_memory_candidates("My name is Gajendra")
    assert cands
    assert "Gajendra" in cands[0]["content"]
    memories = [{"content": "User's name is Gajendra.", "enabled": 1}]
    assert aligned_memory_reply("What is my name?", memories) == "Your name is Gajendra."


def test_enrich_saves_and_recalls(tmp_path, monkeypatch):
    db = tmp_path / "om.sqlite3"
    monkeypatch.setenv("OM_AI_DB", str(db))
    # Reset platform store singleton
    import om_ai.api.platform_store as ps

    ps._store = None

    actor = "user:test1"
    b1 = enrich_for_chat(
        [{"role": "user", "content": "My name is Gajendra"}],
        tenant_id="default",
        actor=actor,
    )
    assert b1.meta.get("saved_memories")

    b2 = enrich_for_chat(
        [{"role": "user", "content": "What is my name?"}],
        tenant_id="default",
        actor=actor,
    )
    assert b2.direct_reply == "Your name is Gajendra."
    assert "Follow" in language_instruction("en") or "English" in language_instruction("en")
