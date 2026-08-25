from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json, math, os, pickle, random, time
import numpy as np
import torch
from torch.utils.data import DataLoader

from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer
from om_ai.tokenizer import ByteBPETokenizer
from om_ai.data import DatasetPipeline, TokenBlockDataset


@dataclass(slots=True)
class TrainingConfig:
    steps: int = 1000
    batch_size: int = 4
    grad_accum_steps: int = 1
    learning_rate: float = 3e-4
    min_lr_ratio: float = 0.1
    warmup_steps: int = 100
    weight_decay: float = 0.1
    grad_clip: float = 1.0
    precision: str = "auto"  # auto|fp32|fp16|bf16
    checkpoint_every: int = 100
    log_every: int = 10
    output_dir: str = "artifacts/checkpoints"
    seed: int = 42
    num_workers: int = 0
    keep_last_step_checkpoints: int = 2
    min_free_gb: float = 1.0


class Trainer:
    def __init__(self, model: OMTransformer, train_cfg: TrainingConfig, device: str | None = None):
        self.model = model
        self.cfg = train_cfg
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"))
        self.model.to(self.device)
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=train_cfg.learning_rate, weight_decay=train_cfg.weight_decay)
        self.global_step = 0
        self._seed(train_cfg.seed)

    @staticmethod
    def _seed(seed):
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
        if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)

    def _amp_dtype(self):
        if self.cfg.precision == "fp32":
            return None
        if self.cfg.precision == "bf16":
            return torch.bfloat16
        if self.cfg.precision == "fp16":
            return torch.float16
        if self.cfg.precision == "auto":
            if self.device.type == "cuda":
                return torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
            if self.device.type == "mps":
                return torch.float16
        return None

    def _lr(self, step):
        if step < self.cfg.warmup_steps:
            return self.cfg.learning_rate * (step + 1) / max(1, self.cfg.warmup_steps)
        progress = (step - self.cfg.warmup_steps) / max(1, self.cfg.steps - self.cfg.warmup_steps)
        cosine = 0.5 * (1 + math.cos(math.pi * min(1.0, progress)))
        return self.cfg.learning_rate * (self.cfg.min_lr_ratio + (1 - self.cfg.min_lr_ratio) * cosine)

    @staticmethod
    def _free_bytes(path: Path) -> int | None:
        try:
            usage = os.statvfs(path)
            return int(usage.f_bavail * usage.f_frsize)
        except OSError:
            return None

    def _ensure_disk_space(self, path: Path) -> None:
        free = self._free_bytes(path.parent if path.suffix else path)
        need = int(max(0.5, float(self.cfg.min_free_gb)) * (1024**3))
        if free is not None and free < need:
            free_gb = free / (1024**3)
            raise RuntimeError(
                f"Not enough disk space to save checkpoint at {path} "
                f"(free={free_gb:.2f} GiB, need>={self.cfg.min_free_gb} GiB). "
                f"Delete old artifacts/checkpoints/*/step-*.pt or unused runs, then retry."
            )

    def _prune_step_checkpoints(self) -> None:
        keep = max(0, int(self.cfg.keep_last_step_checkpoints))
        root = Path(self.cfg.output_dir)
        steps = sorted(
            root.glob("step-*.pt"),
            key=lambda p: p.stat().st_mtime,
        )
        for old in steps[:-keep] if keep else steps:
            try:
                old.unlink(missing_ok=True)
            except OSError:
                pass

    def save_checkpoint(self, path: str | Path, extra: dict | None = None):
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_disk_space(p)
        payload = {
            "model": self.model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "global_step": self.global_step,
            "model_config": asdict(self.model.cfg),
            "train_config": asdict(self.cfg),
            "extra": extra or {},
        }
        # Atomic write: avoid truncated latest.pt if training is interrupted mid-save.
        tmp = p.with_name(f".{p.name}.{os.getpid()}.tmp")
        try:
            torch.save(payload, tmp)
            os.replace(tmp, p)
        except Exception as exc:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            msg = str(exc).lower()
            if "iostream" in msg or "unexpected pos" in msg or "no space" in msg:
                raise RuntimeError(
                    f"Checkpoint write failed (often disk full) while saving {p}: {exc}. "
                    f"Free space under artifacts/checkpoints/ and retry with --resume."
                ) from exc
            raise
        finally:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
        if p.name.startswith("step-"):
            self._prune_step_checkpoints()

    def load_checkpoint(self, path: str | Path):
        p = Path(path)
        try:
            if not p.is_file() or p.stat().st_size == 0:
                raise EOFError("empty or missing checkpoint")
            ckpt = torch.load(p, map_location=self.device, weights_only=False)
        except (EOFError, pickle.UnpicklingError, RuntimeError) as e:
            # RuntimeError: pytorch sometimes wraps truncated zip / pickle failures.
            msg = str(e).lower()
            if isinstance(e, RuntimeError) and "pickle" not in msg and "eof" not in msg and "zip" not in msg:
                raise
            raise ValueError(
                f"Corrupt checkpoint at {p}; remove --resume or delete file and restart."
            ) from e
        self.model.load_state_dict(ckpt["model"])
        if "optimizer" in ckpt:
            self.optimizer.load_state_dict(ckpt["optimizer"])
        self.global_step = int(ckpt.get("global_step", 0))

    def train(self, dataset: TokenBlockDataset):
        loader = DataLoader(dataset, batch_size=self.cfg.batch_size, shuffle=True, num_workers=self.cfg.num_workers, drop_last=False)
        iterator = iter(loader)
        amp_dtype = self._amp_dtype()
        scaler = torch.amp.GradScaler("cuda", enabled=(amp_dtype == torch.float16 and self.device.type == "cuda"))
        self.model.train()
        self.optimizer.zero_grad(set_to_none=True)
        start = time.time()

        while self.global_step < self.cfg.steps:
            total_loss = 0.0
            for _ in range(self.cfg.grad_accum_steps):
                try:
                    x, y = next(iterator)
                except StopIteration:
                    iterator = iter(loader); x, y = next(iterator)
                x, y = x.to(self.device), y.to(self.device)
                use_autocast = amp_dtype is not None and self.device.type in {"cuda", "mps", "cpu"}
                context = torch.autocast(
                    device_type=self.device.type,
                    dtype=amp_dtype,
                    enabled=use_autocast,
                )
                with context:
                    out = self.model(x, labels=y)
                    loss = out["loss"] / self.cfg.grad_accum_steps
                if scaler.is_enabled():
                    scaler.scale(loss).backward()
                else:
                    loss.backward()
                total_loss += float(loss.detach())

            if scaler.is_enabled():
                scaler.unscale_(self.optimizer)
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.cfg.grad_clip)
            lr = self._lr(self.global_step)
            for group in self.optimizer.param_groups:
                group["lr"] = lr
            if scaler.is_enabled():
                scaler.step(self.optimizer)
                scaler.update()
            else:
                self.optimizer.step()
            self.optimizer.zero_grad(set_to_none=True)
            self.global_step += 1

            if self.global_step % self.cfg.log_every == 0 or self.global_step == 1:
                elapsed = max(1e-6, time.time() - start)
                print(
                    json.dumps(
                        {
                            "step": self.global_step,
                            "loss": round(total_loss, 5),
                            "lr": lr,
                            "steps_per_sec": round(self.global_step / elapsed, 3),
                        }
                    ),
                    flush=True,
                )
            if self.global_step % self.cfg.checkpoint_every == 0:
                self.save_checkpoint(Path(self.cfg.output_dir) / f"step-{self.global_step}.pt")
                self.save_checkpoint(Path(self.cfg.output_dir) / "latest.pt")

        self.save_checkpoint(Path(self.cfg.output_dir) / "latest.pt")
        return {"steps": self.global_step, "last_loss": total_loss}


def build_dataset(
    data_path: str,
    tokenizer: ByteBPETokenizer,
    seq_len: int,
    *,
    max_tokens: int | None = None,
    max_docs: int | None = None,
) -> TokenBlockDataset:
    """Build token blocks via streaming load (no full multi-GB ``read_text``)."""
    pipe = DatasetPipeline()
    records = pipe.iter_process(DatasetPipeline.iter_load(data_path))
    ids = DatasetPipeline.tokenize_streaming(
        records,
        tokenizer,
        max_tokens=max_tokens,
        max_docs=max_docs,
    )
    return TokenBlockDataset(ids, seq_len=seq_len)
