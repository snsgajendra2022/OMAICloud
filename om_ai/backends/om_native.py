from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Generator

import torch

from om_ai.backends.base import NativeCheckpointError
from om_ai.runtime.engine import LocalLLMEngine
from om_ai.tokenizer import load_tokenizer, tokenizer_fingerprint

logger = logging.getLogger(__name__)

OM_MODEL_NAME = "OM-1.0"
OM_PROVIDER = "OM AI"
OM_BACKEND_ID = "om_native"


def pick_device(preferred: str | None = None) -> torch.device:
    """Honest device selection: CUDA → MPS → CPU (never fake CUDA)."""
    if preferred:
        pref = preferred.strip().lower()
        if pref == "cuda":
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA requested but torch.cuda.is_available() is False")
            return torch.device("cuda")
        if pref == "mps":
            if not torch.backends.mps.is_available():
                raise RuntimeError("MPS requested but torch.backends.mps.is_available() is False")
            return torch.device("mps")
        if pref == "cpu":
            return torch.device("cpu")
        return torch.device(preferred)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def default_native_paths() -> dict[str, str]:
    """Resolve OM-1.0 paths from env (OM_MODEL_* preferred, OM_AI_* fallback).

    Checkpoint preference when unset: ``om-1.0-long`` → registry → ``om-1.0-smoke``.
    """
    root = Path(__file__).resolve().parents[2]
    config = (
        os.getenv("OM_MODEL_CONFIG")
        or os.getenv("OM_AI_CONFIG")
        or str(root / "configs" / "om-1.0-local.json")
    )
    tokenizer = (
        os.getenv("OM_MODEL_TOKENIZER")
        or os.getenv("OM_AI_TOKENIZER")
        or str(root / "artifacts" / "tokenizer-fixed-v3.json")
    )
    checkpoint = (
        os.getenv("OM_MODEL_CHECKPOINT")
        or os.getenv("OM_AI_CHECKPOINT")
        or ""
    )
    if not checkpoint:
        from om_ai.backends.om_registry import pick_best_checkpoint

        best = pick_best_checkpoint(root)
        if best is not None:
            checkpoint = str(best)
        else:
            candidates = [
                root / "artifacts" / "checkpoints" / "om-1.0-long" / "latest.pt",
                root / "artifacts" / "models" / "om-1.0" / "checkpoint.pt",
                root / "artifacts" / "checkpoints" / "om-1.0-smoke" / "latest.pt",
            ]
            for c in candidates:
                if c.is_file():
                    checkpoint = str(c)
                    break
    return {
        "config": config,
        "tokenizer": tokenizer,
        "checkpoint": checkpoint,
        "device": (os.getenv("OM_MODEL_DEVICE") or os.getenv("OM_AI_DEVICE") or "").strip(),
    }


class OMNativeBackend:
    """OM-1.0 native inference — LocalLLMEngine / OMTransformer only. No Ollama proxy."""

    def __init__(self, engine: LocalLLMEngine | None = None):
        self.engine = engine or LocalLLMEngine()
        self._trained = False
        self._load_error: str | None = None
        self._paths: dict[str, str] = {}

    @property
    def loaded(self) -> bool:
        return self.engine.model is not None and self.engine.tokenizer is not None

    def load(
        self,
        config_path: str | None = None,
        tokenizer_path: str | None = None,
        checkpoint_path: str | None = None,
        device: str | None = None,
        *,
        require_checkpoint: bool = True,
    ) -> dict[str, Any]:
        paths = default_native_paths()
        config_path = config_path or paths["config"]
        tokenizer_path = tokenizer_path or paths["tokenizer"]
        checkpoint_path = checkpoint_path or paths["checkpoint"]
        device = device or paths["device"] or None
        self._paths = {
            "config": config_path,
            "tokenizer": tokenizer_path,
            "checkpoint": checkpoint_path or "",
            "device": device or "",
        }

        if require_checkpoint and (not checkpoint_path or not Path(checkpoint_path).is_file()):
            self._trained = False
            self._load_error = "OM-1.0 checkpoint unavailable."
            raise NativeCheckpointError(self._load_error)

        # Bind tokenizer_sha256 from registry only when loading that same checkpoint.
        try:
            from om_ai.backends.om_registry import load_registry_metadata

            reg = load_registry_metadata()
            reg_ckpt = str(reg.get("checkpoint") or "") if reg else ""
            same_ckpt = bool(
                reg_ckpt
                and checkpoint_path
                and Path(reg_ckpt).resolve() == Path(checkpoint_path).resolve()
            )
            if same_ckpt and reg and tokenizer_path and Path(tokenizer_path).is_file():
                expected = reg.get("tokenizer_sha256") or reg.get("tokenizer_fingerprint")
                actual = tokenizer_fingerprint(tokenizer_path)
                if expected and expected != actual:
                    raise NativeCheckpointError(
                        f"OM-1.0 tokenizer_sha256 mismatch: registry={expected}, "
                        f"loaded={actual}"
                    )
        except NativeCheckpointError:
            raise
        except Exception:
            pass

        try:
            info = self.engine.load(
                config_path,
                tokenizer_path,
                checkpoint_path,
                str(pick_device(device)) if device else None,
            )
        except Exception as exc:
            self._trained = False
            self._load_error = str(exc)
            # Never fall back to Ollama / third-party LLMs.
            raise NativeCheckpointError(
                f"OM-1.0 checkpoint unavailable. ({exc})"
            ) from exc

        # trained=true ONLY when a real training checkpoint was loaded (file existed).
        self._trained = bool(checkpoint_path and Path(checkpoint_path).is_file())
        self._load_error = None
        info["trained"] = self._trained
        info["name"] = OM_MODEL_NAME
        info["provider"] = OM_PROVIDER
        info["backend"] = OM_BACKEND_ID
        info["tokenizer_sha256"] = info.get("tokenizer_fingerprint")
        return info

    def ensure_loaded(self) -> None:
        if self.loaded and self._trained:
            return
        self.load(require_checkpoint=True)

    def generate(self, prompt: str, **kwargs: Any) -> str:
        self.ensure_loaded()
        return self.engine.generate(prompt, **kwargs)

    def chat(self, messages: list[dict], **kwargs: Any) -> str:
        self.ensure_loaded()
        return self.engine.chat(messages, **kwargs)

    def stream_chat(self, messages: list[dict], **kwargs: Any) -> Generator[str, None, None]:
        """Best-effort streaming: chat encode then token stream via generate_stream path."""
        self.ensure_loaded()
        # Prefer non-stream chat if tokenizer lacks token_bytes.
        if not hasattr(self.engine.tokenizer, "token_bytes"):
            yield self.engine.chat(messages, **kwargs)
            return

        import codecs

        from om_ai.runtime.engine import (
            EMPTY_GENERATION_FALLBACK,
            fit_messages_to_context,
            usable_generation_text,
        )

        tok = self.engine.tokenizer
        fitted = fit_messages_to_context(
            messages, tok, self.engine.model.cfg.max_seq_len
        )
        ids = tok.encode_chat(fitted, add_generation_prompt=True, add_eos=False)
        ids = ids[-self.engine.model.cfg.max_seq_len :]
        x = torch.tensor([ids], device=self.engine.device)
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        stops = set()
        if getattr(tok, "assistant_end_id", None) is not None:
            stops.add(int(tok.assistant_end_id))
        stops.add(int(tok.eos_id))
        min_new = int(kwargs.get("min_new_tokens", 4))
        emitted: list[str] = []

        for step, token_tensor in enumerate(
            self.engine.model.generate_stream(
                x,
                max_new_tokens=kwargs.get("max_new_tokens", 256),
                temperature=kwargs.get("temperature", 0.7),
                top_k=kwargs.get("top_k", 50),
                top_p=kwargs.get("top_p", 0.9),
                repetition_penalty=kwargs.get("repetition_penalty", 1.2),
                eos_token_id=tok.eos_id,
                stop_token_ids=list(stops - {int(tok.eos_id)}),
                min_new_tokens=min_new,
                no_repeat_ngram_size=int(kwargs.get("no_repeat_ngram_size", 3)),
                repetition_window=int(kwargs.get("repetition_window", 128)),
            )
        ):
            token_id = int(token_tensor.view(-1)[0])
            if token_id in stops and step >= min_new:
                break
            raw = tok.token_bytes(token_id)
            if not raw:
                continue
            chunk = decoder.decode(raw, final=False)
            if chunk:
                emitted.append(chunk)
                yield chunk
        tail = decoder.decode(b"", final=True)
        if tail:
            emitted.append(tail)
            yield tail
        if not emitted:
            yield EMPTY_GENERATION_FALLBACK
        elif not usable_generation_text("".join(emitted)):
            # Stream already flushed garbage; surface an honest recovery hint.
            yield "\n" + EMPTY_GENERATION_FALLBACK

    def health(self) -> dict[str, Any]:
        ckpt = self._paths.get("checkpoint") or default_native_paths()["checkpoint"]
        ckpt_ok = bool(ckpt and Path(ckpt).is_file())
        return {
            "ok": self.loaded and self._trained and ckpt_ok,
            "backend": OM_BACKEND_ID,
            "name": OM_MODEL_NAME,
            "provider": OM_PROVIDER,
            "loaded": self.loaded,
            "trained": self._trained,
            "checkpoint_present": ckpt_ok,
            "checkpoint": ckpt or None,
            "device": str(self.engine.device) if self.engine.device is not None else None,
            "error": self._load_error,
        }

    def model_info(self) -> dict[str, Any]:
        base = {
            "name": OM_MODEL_NAME,
            "provider": OM_PROVIDER,
            "backend": OM_BACKEND_ID,
            "trained": bool(self._trained and self.loaded),
            "loaded": self.loaded,
        }
        if not self.loaded:
            paths = self._paths or default_native_paths()
            base.update(
                {
                    "config_path": paths.get("config"),
                    "tokenizer_path": paths.get("tokenizer"),
                    "checkpoint_path": paths.get("checkpoint") or None,
                    "lifecycle": (
                        "checkpoint_available"
                        if paths.get("checkpoint") and Path(paths["checkpoint"]).is_file()
                        else "architecture_created"
                    ),
                }
            )
            return base

        info = self.engine.info()
        tok_path = self._paths.get("tokenizer") or ""
        fp = None
        if tok_path and Path(tok_path).is_file():
            fp = tokenizer_fingerprint(tok_path)
        elif getattr(self.engine.tokenizer, "fingerprint", None):
            fp = self.engine.tokenizer.fingerprint
        base.update(
            {
                "device": info.get("device"),
                "parameters": info.get("parameters"),
                "vocab_size": info.get("vocab_size"),
                "config_path": info.get("config_path"),
                "tokenizer_path": tok_path or None,
                "checkpoint_path": info.get("checkpoint_path"),
                "tokenizer_fingerprint": fp,
                "tokenizer_info": info.get("tokenizer_info"),
                "lifecycle": "checkpoint_available" if self._trained else "architecture_created",
            }
        )
        return base


def try_load_native_from_env(engine: LocalLLMEngine | None = None) -> OMNativeBackend:
    """Construct backend and load if checkpoint exists; else leave unloaded."""
    backend = OMNativeBackend(engine=engine)
    paths = default_native_paths()
    if paths["checkpoint"] and Path(paths["checkpoint"]).is_file():
        backend.load(
            paths["config"],
            paths["tokenizer"],
            paths["checkpoint"],
            paths["device"] or None,
            require_checkpoint=True,
        )
    else:
        backend._paths = paths
        backend._load_error = "OM-1.0 checkpoint unavailable."
        backend._trained = False
    return backend
