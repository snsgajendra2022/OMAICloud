from __future__ import annotations
import torch
from torch.utils.data import Dataset


class TokenBlockDataset(Dataset):
    def __init__(self, token_ids: list[int], seq_len: int):
        if len(token_ids) < seq_len + 1:
            # Allow tiny smoke corpora by repeating tokens.
            repeats = (seq_len + 2) // max(1, len(token_ids)) + 1
            token_ids = (token_ids * repeats)[: seq_len + 2]
        self.tokens = torch.tensor(token_ids, dtype=torch.long)
        self.seq_len = seq_len

    def __len__(self):
        return max(1, (len(self.tokens) - 1) // self.seq_len)

    def __getitem__(self, idx):
        start = idx * self.seq_len
        chunk = self.tokens[start: start + self.seq_len + 1]
        if len(chunk) < self.seq_len + 1:
            start = max(0, len(self.tokens) - self.seq_len - 1)
            chunk = self.tokens[start: start + self.seq_len + 1]
        return chunk[:-1], chunk[1:]
