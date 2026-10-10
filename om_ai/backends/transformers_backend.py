"""Optional Hugging Face Transformers runtime for pretrained open-weight LLMs.

This is intentionally separate from OMNativeBackend: a pretrained model must use
its own tokenizer and chat template. It never silently falls back to OM-1.0.
Install the optional dependencies before selecting this provider.
"""
from __future__ import annotations

import logging
import os
import threading
from pathlib import Path
from typing import Any, Generator

logger = logging.getLogger(__name__)


class TransformersBackendError(RuntimeError):
    """A configured Transformers model could not be loaded or used."""


class TransformersBackend:
    """Inference adapter for a local or Hugging Face Transformers causal LM.

    Environment:
      OM_HF_MODEL: model ID or local model directory (required)
      OM_HF_DEVICE_MAP: device map (default: auto)
      OM_HF_DTYPE: auto, float16, bfloat16, or float32 (default: auto)
      OM_HF_QUANTIZATION: none, 4bit, or 8bit (default: none)
      OM_HF_TRUST_REMOTE_CODE: must be explicitly true to allow custom code
      OM_HF_MAX_MEMORY: optional JSON device-memory map for device_map=auto
    """

    def __init__(self) -> None:
        self.model: Any = None
        self.tokenizer: Any = None
        self.model_id: str | None = None
        self.device_map: str = "auto"
        self.quantization: str = "none"
        self.parameter_count: int | None = None
        self._load_error: str | None = None

    @staticmethod
    def _dtype(name: str, torch: Any) -> Any:
        values = {
            "auto": "auto",
            "float16": torch.float16,
            "fp16": torch.float16,
            "bfloat16": torch.bfloat16,
            "bf16": torch.bfloat16,
            "float32": torch.float32,
            "fp32": torch.float32,
        }
        try:
            return values[name.strip().lower()]
        except KeyError as exc:
            raise ValueError("OM_HF_DTYPE must be auto, float16, bfloat16, or float32") from exc

    def load(
        self,
        model_id: str | None = None,
        *,
        device_map: str | None = None,
        dtype: str | None = None,
        quantization: str | None = None,
        trust_remote_code: bool | None = None,
        local_files_only: bool = False,
        max_memory: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Load the configured pretrained model and report its actual parameter count."""
        resolved_id = (model_id or os.getenv("OM_HF_MODEL", "")).strip()
        if not resolved_id:
            raise TransformersBackendError(
                "Set OM_HF_MODEL to a licensed model ID or local model directory."
            )
        resolved_device_map = device_map or os.getenv("OM_HF_DEVICE_MAP", "auto")
        resolved_quant = (quantization or os.getenv("OM_HF_QUANTIZATION", "none")).lower()
        allow_remote_code = (
            trust_remote_code
            if trust_remote_code is not None
            else os.getenv("OM_HF_TRUST_REMOTE_CODE", "false").lower() in {"1", "true", "yes"}
        )
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise TransformersBackendError(
                "Transformers provider dependencies are missing. Install the 'hf' extra."
            ) from exc

        if resolved_quant not in {"none", "4bit", "8bit"}:
            raise ValueError("quantization must be none, 4bit, or 8bit")

        kwargs: dict[str, Any] = {
            "device_map": resolved_device_map,
            "torch_dtype": self._dtype(dtype or os.getenv("OM_HF_DTYPE", "auto"), torch),
            "trust_remote_code": bool(allow_remote_code),
            "local_files_only": local_files_only,
        }
        if max_memory:
            kwargs["max_memory"] = max_memory
        elif os.getenv("OM_HF_MAX_MEMORY"):
            import json
            kwargs["max_memory"] = json.loads(os.environ["OM_HF_MAX_MEMORY"])

        if resolved_quant != "none":
            try:
                from transformers import BitsAndBytesConfig
            except ImportError as exc:
                raise TransformersBackendError(
                    "Quantization requires a Transformers version with BitsAndBytesConfig."
                ) from exc
            try:
                import bitsandbytes  # noqa: F401
            except ImportError as exc:
                raise TransformersBackendError(
                    "Install bitsandbytes on a supported CUDA/Linux environment for 4-bit/8-bit loading."
                ) from exc
            kwargs.pop("torch_dtype", None)
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=resolved_quant == "4bit",
                load_in_8bit=resolved_quant == "8bit",
                bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )

        try:
            tokenizer = AutoTokenizer.from_pretrained(
                resolved_id,
                trust_remote_code=bool(allow_remote_code),
                local_files_only=local_files_only,
            )
            model = AutoModelForCausalLM.from_pretrained(resolved_id, **kwargs)
            model.eval()
        except Exception as exc:
            self._load_error = f"{type(exc).__name__}: {exc}"
            raise TransformersBackendError(
                f"Could not load configured model {resolved_id!r}: {type(exc).__name__}: {exc}"
            ) from exc

        count = sum(int(p.numel()) for p in model.parameters())
        self.model = model
        self.tokenizer = tokenizer
        self.model_id = resolved_id
        self.device_map = resolved_device_map
        self.quantization = resolved_quant
        self.parameter_count = count
        self._load_error = None
        return self.model_info()

    def _require_loaded(self) -> tuple[Any, Any]:
        if self.model is None or self.tokenizer is None:
            raise TransformersBackendError("Transformers model is not loaded.")
        return self.model, self.tokenizer

    @staticmethod
    def _validate_messages(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
        if not isinstance(messages, list) or not messages:
            raise ValueError("messages must be a non-empty list")
        allowed = {"system", "developer", "user", "assistant", "tool"}
        normalized: list[dict[str, str]] = []
        for index, item in enumerate(messages):
            if not isinstance(item, dict):
                raise ValueError(f"messages[{index}] must be an object")
            role = str(item.get("role", "")).strip().lower()
            content = item.get("content", "")
            if role not in allowed:
                raise ValueError(f"messages[{index}].role is unsupported: {role!r}")
            if not isinstance(content, str):
                raise ValueError(f"messages[{index}].content must be a string")
            normalized.append({"role": role, "content": content})
        return normalized

    def _inputs(self, messages: list[dict[str, Any]]) -> tuple[Any, Any, Any]:
        model, tokenizer = self._require_loaded()
        safe_messages = self._validate_messages(messages)
        if not getattr(tokenizer, "chat_template", None):
            raise TransformersBackendError(
                "This tokenizer has no chat_template. Configure a model-specific template; refusing to guess one."
            )
        try:
            encoded = tokenizer.apply_chat_template(
                safe_messages,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt",
                return_dict=True,
            )
        except Exception as exc:
            raise TransformersBackendError(f"Model chat-template formatting failed: {exc}") from exc
        # With device_map=auto, inputs belong on the input embedding's device.
        input_device = model.get_input_embeddings().weight.device
        encoded = {key: value.to(input_device) for key, value in encoded.items() if hasattr(value, "to")}
        return model, tokenizer, encoded

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.0,
        do_sample: bool | None = None,
        **_: Any,
    ) -> str:
        import torch
        model, tokenizer, inputs = self._inputs(messages)
        if not 1 <= int(max_new_tokens) <= 32768:
            raise ValueError("max_new_tokens must be between 1 and 32768")
        if not 0 <= float(top_p) <= 1:
            raise ValueError("top_p must be between 0 and 1")
        sampling = bool(temperature > 0) if do_sample is None else bool(do_sample)
        generation: dict[str, Any] = {
            **inputs,
            "max_new_tokens": int(max_new_tokens),
            "do_sample": sampling,
            "repetition_penalty": max(0.1, float(repetition_penalty)),
            "use_cache": True,
        }
        if sampling:
            generation["temperature"] = max(0.01, float(temperature))
            generation["top_p"] = float(top_p)
            if int(top_k) > 0:
                generation["top_k"] = int(top_k)
        eos = tokenizer.eos_token_id
        if eos is not None:
            generation["eos_token_id"] = eos
        if tokenizer.pad_token_id is not None:
            generation["pad_token_id"] = tokenizer.pad_token_id
        with torch.inference_mode():
            output = model.generate(**generation)
        prompt_len = inputs["input_ids"].shape[-1]
        new_tokens = output[0, prompt_len:]
        return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    def generate(self, prompt: str, **kwargs: Any) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        return self.chat([{"role": "user", "content": prompt}], **kwargs)

    def stream_chat(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> Generator[str, None, None]:
        try:
            import torch
            from transformers import TextIteratorStreamer
        except ImportError as exc:
            raise TransformersBackendError(
                "Streaming requires the optional Transformers dependencies."
            ) from exc
        model, tokenizer, inputs = self._inputs(messages)
        max_new_tokens = int(kwargs.pop("max_new_tokens", 512))
        temperature = float(kwargs.pop("temperature", 0.7))
        top_p = float(kwargs.pop("top_p", 0.9))
        top_k = int(kwargs.pop("top_k", 50))
        repetition_penalty = float(kwargs.pop("repetition_penalty", 1.0))
        if not 1 <= max_new_tokens <= 32768:
            raise ValueError("max_new_tokens must be between 1 and 32768")
        sampling = bool(temperature > 0)
        args: dict[str, Any] = {
            **inputs,
            "max_new_tokens": max_new_tokens,
            "do_sample": sampling,
            "repetition_penalty": max(0.1, repetition_penalty),
            "use_cache": True,
        }
        if sampling:
            args.update(temperature=max(0.01, temperature), top_p=top_p)
            if top_k > 0:
                args["top_k"] = top_k
        if tokenizer.eos_token_id is not None:
            args["eos_token_id"] = tokenizer.eos_token_id
        if tokenizer.pad_token_id is not None:
            args["pad_token_id"] = tokenizer.pad_token_id
        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True, timeout=120.0)
        args["streamer"] = streamer
        errors: list[BaseException] = []

        def worker() -> None:
            try:
                with torch.inference_mode():
                    model.generate(**args)
            except BaseException as exc:
                errors.append(exc)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        try:
            for piece in streamer:
                if piece:
                    yield piece
            thread.join(timeout=5)
            if errors:
                raise TransformersBackendError(f"Streaming generation failed: {errors[0]}") from errors[0]
        finally:
            # Transformers' streamer has no universal cancellation API; a timeout is
            # bounded at the consumer side but cannot guarantee kernel cancellation.
            if thread.is_alive():
                logger.warning("Generation worker still active after stream consumer closed")

    def stream_generate(self, prompt: str, **kwargs: Any) -> Generator[str, None, None]:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        yield from self.stream_chat([{"role": "user", "content": prompt}], **kwargs)

    def health(self) -> dict[str, Any]:
        return {
            "ok": self.model is not None and self.tokenizer is not None,
            "provider": "transformers",
            "model_id": self.model_id,
            "parameter_count": self.parameter_count,
            "quantization": self.quantization,
            "device_map": self.device_map,
            "error": self._load_error,
        }

    def model_info(self) -> dict[str, Any]:
        return {
            **self.health(),
            "parameters_billions": (
                round(self.parameter_count / 1_000_000_000, 3)
                if self.parameter_count is not None else None
            ),
            "tokenizer_class": type(self.tokenizer).__name__ if self.tokenizer is not None else None,
            "chat_template_available": bool(getattr(self.tokenizer, "chat_template", None)),
            "model_type": getattr(getattr(self.model, "config", None), "model_type", None),
        }
