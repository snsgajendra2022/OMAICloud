import json
from pathlib import Path

import pytest

from om_ai.tokenizer import ByteBPETokenizer
from om_ai.tokenizer.byte_bpe import SPECIAL_TOKENS


def test_roundtrip_unicode():
    text = "Hello OM AI — नमस्ते"
    tok = ByteBPETokenizer.train([text, text], vocab_size=300, min_pair_freq=1)
    assert tok.decode(tok.encode(text)) == text


def test_load_om_format_roundtrip(tmp_path: Path):
    text = "OM ByteBPE load test"
    tok = ByteBPETokenizer.train([text], vocab_size=300, min_pair_freq=1)
    path = tmp_path / "om-tok.json"
    tok.save(path)
    loaded = ByteBPETokenizer.load(path)
    assert loaded.vocab == tok.vocab
    assert loaded.merges == tok.merges
    assert loaded.decode(loaded.encode(text)) == text


def test_load_huggingface_format_raises_clear_error(tmp_path: Path):
    path = tmp_path / "hf-tok.json"
    path.write_text(
        json.dumps(
            {
                "version": "1.0",
                "truncation": None,
                "padding": None,
                "added_tokens": [{"id": 0, "content": "<pad>", "special": True}],
                "normalizer": {"type": "NFKC"},
                "pre_tokenizer": {"type": "ByteLevel"},
                "model": {"type": "BPE", "vocab": {}, "merges": []},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not OM ByteBPE|HuggingFace|vocab.*merges") as exc:
        ByteBPETokenizer.load(path)
    msg = str(exc.value)
    assert "vocab" in msg and "merges" in msg
    assert "HuggingFace" in msg or "om-ai tokenizer train" in msg


def test_base_includes_chat_specials():
    tok = ByteBPETokenizer.base()
    for t in SPECIAL_TOKENS:
        assert t in tok.vocab
    assert tok.inspect()["chat_tokens_available"] is True


def test_encode_chat_inference_ends_at_assistant_open():
    tok = ByteBPETokenizer.base()
    ids = tok.encode_chat(
        [
            {"role": "system", "content": "You are Memories Assistant."},
            {"role": "user", "content": "What project are you currently working with?"},
        ],
        add_generation_prompt=True,
    )
    assert ids[0] == tok.bos_id
    assert ids[-1] == tok.assistant_id
    assert tok.eos_id not in ids
    assert ids.count(tok.system_id) == 1
    assert ids.count(tok.system_end_id) == 1
    assert ids.count(tok.user_id) == 1
    assert ids.count(tok.user_end_id) == 1
    # Role markers are special IDs, not UTF-8 byte encodings of "<system>" text.
    literal = tok.encode("<system>")
    assert tok.system_id not in literal


def test_encode_chat_training_closes_assistant_and_eos():
    tok = ByteBPETokenizer.base()
    messages = [
        {"role": "system", "content": "You are Memories Assistant."},
        {"role": "user", "content": "What project are you currently working with?"},
        {"role": "assistant", "content": "I am working with the Memories project."},
    ]
    ids = tok.encode_chat(messages, add_generation_prompt=False, add_eos=True)
    assert ids[0] == tok.bos_id
    assert ids[-1] == tok.eos_id
    assert ids[-2] == tok.assistant_end_id
    assert tok.assistant_id in ids


def test_encode_chat_generation_prompt_is_prefix_of_completed():
    tok = ByteBPETokenizer.base()
    prefix_msgs = [
        {"role": "system", "content": "Only use project Memories."},
        {"role": "user", "content": "What project?"},
    ]
    prefix = tok.encode_chat(prefix_msgs, add_generation_prompt=True)
    full = tok.encode_chat(
        prefix_msgs
        + [{"role": "assistant", "content": "I am working with the Memories project."}],
        add_generation_prompt=False,
        add_eos=True,
    )
    assert full[: len(prefix)] == prefix
    # Content after the open <assistant> is response + </assistant> + <eos>
    assert full[len(prefix) : -2] == tok.encode("I am working with the Memories project.")
    assert full[-2:] == [tok.assistant_end_id, tok.eos_id]


def test_encode_chat_does_not_byte_encode_role_tags():
    tok = ByteBPETokenizer.base()
    ids = tok.encode_chat([{"role": "user", "content": "hi"}], add_generation_prompt=True)
    # Exactly one <user>, </user>, <assistant> special — no duplicated byte forms.
    assert ids.count(tok.user_id) == 1
    assert ids.count(tok.user_end_id) == 1
    assert ids.count(tok.assistant_id) == 1
    # Content "hi" is present as bytes, not the string "<user>"
    assert tok.decode(ids) == "hi"
