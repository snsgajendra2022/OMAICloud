from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
import time

import torch
from torch.utils.data import Dataset, DataLoader

from om_ai.model.causal_loss import build_assistant_only_labels


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

            # Preserve a supervised assistant target even when the prompt is longer
            # than the model context. The old implementation truncated the concatenated
            # sequence from the right, which could remove the entire response; it also
            # used the original prompt length after truncation, causing valid rows to
            # receive only -100 labels and contribute no training signal.
            max_seq_len = int(max_seq_len)
            if max_seq_len < 2:
                raise ValueError("SFT max_seq_len must be at least 2")

            # Reserve up to half the context for the completion, so long prompts
            # cannot crowd the assistant target out of the training window.
            target_budget = min(len(response_ids), max(1, max_seq_len // 2))
            target_ids = response_ids[:target_budget]
            if not target_ids:
                skipped += 1
                continue

            # Keep the most recent portion of the chat prefix (usually the user ask).
            prefix_budget = max_seq_len - len(target_ids)
            if prefix_budget <= 0:
                skipped += 1
                continue
            prefix_ids = prefix_ids[-prefix_budget:]
            ids = prefix_ids + target_ids
            labels = build_assistant_only_labels(ids, prompt_len=len(prefix_ids))

            # Fail closed if an example has no assistant tokens after truncation.
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
        from om_ai.training.production_pipeline import pick_training_device

        self.device = torch.device(device or pick_training_device())
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
        temp_target = target.with_name(f".{target.name}.tmp")

        # SFT checkpoints are used to initialize inference or a later training run;
        # the optimizer state is not required by the current CLI loader and can make
        # each file several times larger than the model weights. Save only portable
        # model state and training metadata.
        payload = {
            "model": self.model.state_dict(),
            "stage": "sft",
            "step": step,
            "sft_config": {
                "steps": self.cfg.steps,
                "batch_size": self.cfg.batch_size,
                "grad_accum_steps": self.cfg.grad_accum_steps,
                "learning_rate": self.cfg.learning_rate,
                "precision": self.cfg.precision,
            },
        }

        # Keep the most recent known-good periodic checkpoint while writing the next
        # one. Older periodic files can consume hundreds of MB and cause PyTorch's
        # zip writer to fail on machines with limited free disk space.
        if not final:
            previous = sorted(
                p.glob("step-*.pt"),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
            for stale in previous[1:]:
                try:
                    stale.unlink()
                except OSError:
                    pass

        try:
            torch.save(payload, temp_target)
            # Atomic replacement prevents a failed write from corrupting the last
            # valid checkpoint at the destination.
            os.replace(temp_target, target)
        except Exception as exc:
            try:
                temp_target.unlink(missing_ok=True)
            except OSError:
                pass
            raise RuntimeError(
                f"Could not save SFT checkpoint to {target}. Check free disk space "
                "and write permissions; the previous completed checkpoint is kept."
            ) from exc

        # Once a new periodic checkpoint is safely written, remove the older one.
        if not final:
            for stale in p.glob("step-*.pt"):
                if stale != target:
                    try:
                        stale.unlink()
                    except OSError:
                        pass
        return {"checkpoint": str(target), "steps": step}
