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
        response_ids = self.tok.encode(response)
        if self.tok.assistant_end_id is not None:
            response_ids.append(self.tok.assistant_end_id)
        response_ids.append(self.tok.eos_id)

        ids = (prefix_ids + response_ids)[: self.max_seq_len]
        response_start = min(len(prefix_ids), len(ids))
        mask = [0] * response_start + [1] * max(0, len(ids) - response_start)
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
