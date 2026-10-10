import json

from om_ai.training.sft import SFTDataset


class FakeChatTokenizer:
    pad_id = 0
    eos_id = 2
    assistant_end_id = 9

    def inspect(self):
        return {"chat_tokens_available": True}

    def encode_chat(self, messages, *, add_generation_prompt=True, add_eos=False):
        # Deliberately longer than the test context so the old right-truncation
        # implementation would remove the assistant response completely.
        return [1, 6] + list(range(10, 30)) + [8]

    def encode(self, text):
        return [100 + (ord(char) % 50) for char in text]


def test_sft_keeps_assistant_targets_when_prompt_exceeds_context(tmp_path):
    path = tmp_path / "train.jsonl"
    path.write_text(
        json.dumps({"prompt": "a very long prompt", "response": "TARGET"}),
        encoding="utf-8",
    )

    dataset = SFTDataset(str(path), FakeChatTokenizer(), max_seq_len=8)
    ids, labels = dataset[0]

    assert len(ids) <= 8
    assert len(labels) == len(ids)
    supervised = [token for token in labels if token != -100]
    assert supervised
    # The response is retained as a training target rather than being entirely
    # cut off by prompt truncation.
    assert supervised[0] == ids[len(ids) - len(supervised)]
    assert 9 in supervised or 2 in supervised
