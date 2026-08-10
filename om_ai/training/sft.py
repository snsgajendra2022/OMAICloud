from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json
import torch
from torch.utils.data import Dataset, DataLoader


class SFTDataset(Dataset):
    def __init__(self, path: str, tokenizer, max_seq_len: int):
        self.rows = []
        self.tok = tokenizer
        self.max_seq_len = max_seq_len

        inspect = getattr(tokenizer, "inspect", None)
        chat_ok = bool(inspect().get("chat_tokens_available")) if callable(inspect) else False
        if not chat_ok:
            raise ValueError(
                "SFT requires a tokenizer with chat specials "
                "(<system>, <user>, <assistant>). Train/save a new tokenizer; "
                "do not use the legacy demo vocab that only has pad/bos/eos/unk."
            )

        for line in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            prompt = str(obj.get("prompt", obj.get("instruction", "")))
            response = str(obj.get("response", obj.get("output", "")))
            system = str(obj.get("system", ""))

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            prefix_ids = tokenizer.encode_chat(
                messages,
                add_generation_prompt=True,
                add_eos=False,
            )

            response_ids = tokenizer.encode(response)
            if tokenizer.assistant_end_id is not None:
                response_ids.append(tokenizer.assistant_end_id)
            response_ids.append(tokenizer.eos_id)

            ids = (prefix_ids + response_ids)[:max_seq_len]
            labels = [-100] * min(len(prefix_ids), len(ids))
            labels += ids[len(labels):]

            if len(ids) >= 2 and any(v != -100 for v in labels):
                self.rows.append((ids, labels))

        if not self.rows:
            raise ValueError("No usable SFT rows")

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        return self.rows[idx]

    def collate(self, batch):
        maxlen = max(len(x[0]) for x in batch)
        xs, ys = [], []
        for ids, labels in batch:
            pad = maxlen - len(ids)
            full_ids = ids + [self.tok.pad_id] * pad
            full_labels = labels + [-100] * pad
            xs.append(full_ids[:-1])
            ys.append(full_labels[1:])
        return torch.tensor(xs, dtype=torch.long), torch.tensor(ys, dtype=torch.long)


@dataclass(slots=True)
class SFTConfig:
    steps: int = 1000
    batch_size: int = 2
    learning_rate: float = 2e-5
    grad_clip: float = 1.0
    output_dir: str = "artifacts/sft"
    checkpoint_every: int = 100


class SFTTrainer:
    def __init__(self, model, dataset: SFTDataset, cfg: SFTConfig, device: str | None = None):
        self.model = model
        self.ds = dataset
        self.cfg = cfg
        self.device = torch.device(
            device or (
                "cuda" if torch.cuda.is_available()
                else "mps" if torch.backends.mps.is_available()
                else "cpu"
            )
        )
        self.model.to(self.device)
        self.opt = torch.optim.AdamW(self.model.parameters(), lr=cfg.learning_rate, weight_decay=0.01)

    def train(self):
        loader = DataLoader(self.ds, batch_size=self.cfg.batch_size, shuffle=True, collate_fn=self.ds.collate)
        it = iter(loader)
        step = 0
        last = 0.0
        self.model.train()
        while step < self.cfg.steps:
            try:
                x, y = next(it)
            except StopIteration:
                it = iter(loader)
                x, y = next(it)
            x = x.to(self.device)
            y = y.to(self.device)
            loss = self.model(x, labels=y)["loss"]
            self.opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.grad_clip)
            self.opt.step()
            step += 1
            last = float(loss.detach())
            if step == 1 or step % 10 == 0:
                print(json.dumps({"stage": "sft", "step": step, "loss": round(last, 5)}))
            if step % self.cfg.checkpoint_every == 0:
                self.save(step)
        return self.save(step, final=True) | {"last_loss": last}

    def save(self, step: int, final: bool = False):
        p = Path(self.cfg.output_dir)
        p.mkdir(parents=True, exist_ok=True)
        target = p / ("latest.pt" if final else f"step-{step}.pt")
        torch.save(
            {"model": self.model.state_dict(), "optimizer": self.opt.state_dict(), "stage": "sft", "step": step},
            target,
        )
        return {"checkpoint": str(target), "steps": step}
