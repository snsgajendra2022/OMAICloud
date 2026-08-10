import json

from om_ai.tokenizer import ByteBPETokenizer
from om_ai.training.sft import SFTDataset
from om_ai.training.preference import PreferenceDataset


def test_chat_generation_prompt_ends_with_assistant_token():
    tok = ByteBPETokenizer.base()
    ids = tok.encode_chat(
        [
            {"role": "system", "content": "You are Memories Assistant."},
            {"role": "user", "content": "Hello"},
        ],
        add_generation_prompt=True,
        add_eos=False,
    )
    assert ids[0] == tok.bos_id
    assert ids[-1] == tok.assistant_id
    assert ids[-1] != tok.eos_id


def test_sft_uses_same_chat_special_tokens(tmp_path):
    tok = ByteBPETokenizer.base()
    p = tmp_path / "sft.jsonl"
    p.write_text(
        json.dumps({
            "system": "Use only Memories project data.",
            "prompt": "Which project?",
            "response": "Memories.",
        }) + "\n",
        encoding="utf-8",
    )
    ds = SFTDataset(str(p), tok, 256)
    ids, labels = ds[0]
    idx = ids.index(tok.assistant_id)
    assert all(v == -100 for v in labels[: idx + 1])
    assert any(v != -100 for v in labels[idx + 1 :])


def test_preference_uses_chat_tokens(tmp_path):
    tok = ByteBPETokenizer.base()
    p = tmp_path / "pref.jsonl"
    p.write_text(
        json.dumps({
            "system": "Use only Memories project data.",
            "prompt": "Which project?",
            "chosen": "Memories.",
            "rejected": "Other.",
        }) + "\n",
        encoding="utf-8",
    )
    ds = PreferenceDataset(str(p), tok, 256)
    system, prompt, chosen, _ = ds[0]
    ids, mask = ds.encode_pair(system, prompt, chosen)
    assert tok.assistant_id in ids
    assert sum(mask) > 0
