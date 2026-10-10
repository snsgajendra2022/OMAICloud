from __future__ import annotations
from pathlib import Path
import json
import torch
from torch.utils.data import Dataset


class PreferenceDataset(Dataset):
    def __init__(self, path, tokenizer, max_seq_len):
        self.rows = []
        self.tok = tokenizer
        self.max_seq_len = max_seq_len
        for line in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            self.rows.append((
                str(obj.get("system", "")),
                str(obj["prompt"]),
                str(obj["chosen"]),
                str(obj["rejected"]),
            ))
        if not self.rows:
            raise ValueError("No preference rows")

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        return self.rows[i]

    def encode_pair(self, system, prompt, response):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        prefix_ids = self.tok.encode_chat(
            messages,
            add_generation_prompt=True,
            add_eos=False,
        )
        response_content_ids = self.tok.encode(response)
        stop_ids = []
        if self.tok.assistant_end_id is not None:
            stop_ids.append(self.tok.assistant_end_id)
        stop_ids.append(self.tok.eos_id)
        response_ids = response_content_ids + stop_ids

        max_seq_len = int(self.max_seq_len)
        if max_seq_len < 4:
            raise ValueError("DPO max_seq_len must be at least 4")

        # Keep both the response and its stop markers in the scored region.
        # Truncating prefix+response from the right used to silently drop all
        # completion tokens for long prompts, making DPO preference log-probs zero.
        target_budget = min(len(response_ids), max(2, max_seq_len // 2))
        if len(response_ids) > target_budget:
            content_budget = max(0, target_budget - len(stop_ids))
            response_ids = response_content_ids[:content_budget] + stop_ids

        prefix_budget = max_seq_len - len(response_ids)
        prefix_ids = prefix_ids[-prefix_budget:] if prefix_budget else []
        ids = prefix_ids + response_ids
        response_start = len(prefix_ids)
        mask = [0] * response_start + [1] * len(response_ids)
        return ids, mask

    def collate(self, batch):
        enc = []
        for system, prompt, chosen, rejected in batch:
            enc.append((
                self.encode_pair(system, prompt, chosen),
                self.encode_pair(system, prompt, rejected),
            ))
        maxlen = max(max(len(c[0]), len(r[0])) for c, r in enc)

        def pad(item):
            ids, mask = item
            n = maxlen - len(ids)
            return ids + [self.tok.pad_id] * n, mask + [0] * n

        cids, cm, rids, rm = [], [], [], []
        for c, r in enc:
            a, b = pad(c)
            d, e = pad(r)
            cids.append(a)
            cm.append(b)
            rids.append(d)
            rm.append(e)

        return {
            "chosen_ids": torch.tensor(cids),
            "chosen_mask": torch.tensor(cm, dtype=torch.float32),
            "rejected_ids": torch.tensor(rids),
            "rejected_mask": torch.tensor(rm, dtype=torch.float32),
        }
