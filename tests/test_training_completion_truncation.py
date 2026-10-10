from __future__ import annotations

import json

from om_ai.training.preference import PreferenceDataset
from om_ai.training.sft import SFTDataset


class _TinyChatTokenizer:
    pad_id = 0
    eos_id = 99
    assistant_end_id = 98

    def inspect(self):
        return {"chat_tokens_available": True}

    def encode_chat(self, messages, add_generation_prompt=True, add_eos=False):
        # Intentionally long prefix to verify that training keeps the latest context.
        size = sum(len(str(message.get("content", ""))) for message in messages)
        return [10 + (i % 3) for i in range(max(1, size))]

    def encode(self, text):
        return [1 + (i % 5) for i, _ in enumerate(text)]


def test_sft_truncation_keeps_assistant_end_and_eos(tmp_path):
    data = tmp_path / "sft.jsonl"
    data.write_text(
        json.dumps({"prompt": "p" * 30, "response": "answer" * 20}) + "\n",
        encoding="utf-8",
    )

    ds = SFTDataset(str(data), _TinyChatTokenizer(), max_seq_len=8)
    ids, labels = ds.rows[0]

    assert len(ids) <= 8
    assert ids[-2:] == [98, 99]
    assert labels[-2:] == [98, 99]
    assert any(label != -100 for label in labels)


def test_dpo_truncation_keeps_completion_mask_and_stop_tokens(tmp_path):
    data = tmp_path / "dpo.jsonl"
    data.write_text(
        json.dumps({
            "prompt": "p" * 30,
            "chosen": "good" * 20,
            "rejected": "bad" * 20,
        }) + "\n",
        encoding="utf-8",
    )

    ds = PreferenceDataset(str(data), _TinyChatTokenizer(), max_seq_len=8)
    ids, mask = ds.encode_pair("", "p" * 30, "good" * 20)

    assert len(ids) <= 8
    assert ids[-2:] == [98, 99]
    assert mask[-2:] == [1, 1]
    assert sum(mask) >= 2
    assert sum(mask) < len(mask)
