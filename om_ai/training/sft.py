from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import time

import torch
from torch.utils.data import Dataset, DataLoader


def _row_to_messages(obj: dict) -> tuple[list[dict[str, str]], str]:
    """Normalize JSONL into chat messages + assistant response text.

    Supported shapes:
      - {"system","prompt"|"instruction","response"|"output"}
      - {"messages":[{role,content}, ...]}  (last assistant = target; earlier = context)
    """
    messages_raw = obj.get("messages")
    if isinstance(messages_raw, list) and messages_raw:
        msgs: list[dict[str, str]] = []
        for m in messages_raw:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role") or "user").strip().lower()
            if role not in {"system", "user", "assistant"}:
                role = "user"
            content = str(m.get("content") or "").strip()
            if content:
                msgs.append({"role": role, "content": content})
        if not msgs:
            return [], ""
        # Prefer last assistant turn as the supervised target.
        if msgs[-1]["role"] == "assistant":
            response = msgs[-1]["content"]
            prefix = msgs[:-1]
            if not any(m["role"] == "user" for m in prefix):
                return [], ""
            return prefix, response
        # No trailing assistant → treat as prompt-only (invalid for SFT).
        return [], ""

    prompt = str(obj.get("prompt", obj.get("instruction", ""))).strip()
    response = str(obj.get("response", obj.get("output", ""))).strip()
    system = str(obj.get("system", "")).strip()
    if not prompt or not response:
        return [], ""
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages, response


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

        skipped = 0
        for line in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            messages, response = _row_to_messages(obj)
            if not messages or not response:
                skipped += 1
                continue

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
            labels += ids[len(labels) :]

            if len(ids) >= 2 and any(v != -100 for v in labels):
                self.rows.append((ids, labels))
            else:
                skipped += 1

        if not self.rows:
            raise ValueError(
                f"No usable SFT rows in {path}"
                + (f" ({skipped} skipped)" if skipped else "")
            )

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
    grad_accum_steps: int = 1
    learning_rate: float = 2e-5
    grad_clip: float = 1.0
    precision: str = "auto"  # auto|fp32|fp16|bf16
    output_dir: str = "artifacts/sft"
    checkpoint_every: int = 100
    log_every: int = 10
    warmup_steps: int = 50


class SFTTrainer:
    """Chat SFT with gradient accumulation + device-aware mixed precision."""

    def __init__(self, model, dataset: SFTDataset, cfg: SFTConfig, device: str | None = None):
        self.model = model
        self.ds = dataset
        self.cfg = cfg
        self.device = torch.device(
            device
            or (
                "cuda"
                if torch.cuda.is_available()
                else "mps"
                if torch.backends.mps.is_available()
                else "cpu"
            )
        )
        self.model.to(self.device)
        self.opt = torch.optim.AdamW(
            self.model.parameters(), lr=cfg.learning_rate, weight_decay=0.01
        )

    def _amp_dtype(self) -> torch.dtype | None:
        prec = (self.cfg.precision or "auto").lower()
        if prec == "fp32":
            return None
        if prec == "bf16":
            return torch.bfloat16
        if prec == "fp16":
            return torch.float16
        # auto: maximize Mac/CUDA without forcing unstable dtypes
        if self.device.type == "cuda":
            return torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        if self.device.type == "mps":
            # MPS: fp16 autocast is supported; bf16 support varies by OS/PyTorch.
            return torch.float16
        return None

    def _lr(self, step: int) -> float:
        warm = max(0, int(self.cfg.warmup_steps))
        if warm and step < warm:
            return self.cfg.learning_rate * (step + 1) / warm
        return self.cfg.learning_rate

    def train(self):
        loader = DataLoader(
            self.ds,
            batch_size=self.cfg.batch_size,
            shuffle=True,
            collate_fn=self.ds.collate,
        )
        it = iter(loader)
        step = 0
        last = 0.0
        amp_dtype = self._amp_dtype()
        use_autocast = amp_dtype is not None and self.device.type in {"cuda", "mps", "cpu"}
        use_scaler = amp_dtype == torch.float16 and self.device.type == "cuda"
        scaler = torch.amp.GradScaler("cuda", enabled=use_scaler)
        accum = max(1, int(self.cfg.grad_accum_steps))
        self.model.train()
        self.opt.zero_grad(set_to_none=True)
        start = time.time()

        while step < self.cfg.steps:
            total_loss = 0.0
            for _ in range(accum):
                try:
                    x, y = next(it)
                except StopIteration:
                    it = iter(loader)
                    x, y = next(it)
                x = x.to(self.device, non_blocking=self.device.type == "cuda")
                y = y.to(self.device, non_blocking=self.device.type == "cuda")
                ctx = torch.autocast(
                    device_type=self.device.type,
                    dtype=amp_dtype,
                    enabled=use_autocast,
                )
                with ctx:
                    loss = self.model(x, labels=y)["loss"] / accum
                if use_scaler:
                    scaler.scale(loss).backward()
                else:
                    loss.backward()
                total_loss += float(loss.detach())

            if use_scaler:
                scaler.unscale_(self.opt)
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.grad_clip)
            lr = self._lr(step)
            for group in self.opt.param_groups:
                group["lr"] = lr
            if use_scaler:
                scaler.step(self.opt)
                scaler.update()
            else:
                self.opt.step()
            self.opt.zero_grad(set_to_none=True)

            step += 1
            last = total_loss
            if step == 1 or step % max(1, self.cfg.log_every) == 0:
                elapsed = max(1e-6, time.time() - start)
                print(
                    json.dumps(
                        {
                            "stage": "sft",
                            "step": step,
                            "loss": round(last, 5),
                            "lr": round(lr, 8),
                            "device": self.device.type,
                            "precision": str(amp_dtype).replace("torch.", "")
                            if amp_dtype
                            else "fp32",
                            "grad_accum": accum,
                            "steps_per_sec": round(step / elapsed, 3),
                        }
                    ),
                    flush=True,
                )
            if step % self.cfg.checkpoint_every == 0:
                self.save(step)
        return self.save(step, final=True) | {"last_loss": last}

    def save(self, step: int, final: bool = False):
        p = Path(self.cfg.output_dir)
        p.mkdir(parents=True, exist_ok=True)
        target = p / ("latest.pt" if final else f"step-{step}.pt")
        torch.save(
            {
                "model": self.model.state_dict(),
                "optimizer": self.opt.state_dict(),
                "stage": "sft",
                "step": step,
                "sft_config": {
                    "steps": self.cfg.steps,
                    "batch_size": self.cfg.batch_size,
                    "grad_accum_steps": self.cfg.grad_accum_steps,
                    "learning_rate": self.cfg.learning_rate,
                    "precision": self.cfg.precision,
                },
            },
            target,
        )
        return {"checkpoint": str(target), "steps": step}
