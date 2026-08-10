from __future__ import annotations

import logging
from pathlib import Path
from typing import Generator

import torch

from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer
from om_ai.tokenizer import ByteBPETokenizer

logger = logging.getLogger(__name__)


class LocalLLMEngine:
    """Wraps OMTransformer + ByteBPETokenizer for text generation."""

    def __init__(self) -> None:
        self.model: OMTransformer | None = None
        self.tokenizer: ByteBPETokenizer | None = None
        self.device: torch.device | None = None
        self._config_path: str | None = None
        self._checkpoint_path: str | None = None

    # ------------------------------------------------------------------ #
    #  Load                                                                 #
    # ------------------------------------------------------------------ #

    def load(
        self,
        config_path: str,
        tokenizer_path: str,
        checkpoint_path: str,
        device: str | None = None,
    ) -> dict:
        cfg = ModelConfig.from_json(config_path)
        self.tokenizer = ByteBPETokenizer.load(tokenizer_path, extend_specials=False)
        if cfg.vocab_size != len(self.tokenizer.vocab):
            cfg.vocab_size = len(self.tokenizer.vocab)

        ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        state = ckpt.get("model", ckpt)
        # Old demo checkpoints used LayerNorm (*.bias); newer default is RMSNorm.
        if any(str(k).endswith(".ln1.bias") or str(k) == "final_norm.bias" for k in state):
            cfg.use_rmsnorm = False

        if device:
            self.device = torch.device(device)
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")

        self.model = OMTransformer(cfg).to(self.device)
        missing, unexpected = self.model.load_state_dict(state, strict=False)
        if missing:
            logger.warning("Checkpoint missing keys (non-fatal): %s", missing[:8])
        if unexpected:
            logger.warning("Checkpoint unexpected keys (non-fatal): %s", unexpected[:8])
        self.model.eval()

        self._config_path = config_path
        self._checkpoint_path = checkpoint_path
        logger.info("Model loaded on %s — %d params", self.device, self.model.exact_parameter_count())
        return {"device": str(self.device), "parameters": self.model.exact_parameter_count()}

    def _assert_loaded(self) -> None:
        if self.model is None or self.tokenizer is None:
            raise RuntimeError(
                "Model is not loaded. Call load() before generating."
            )

    # ------------------------------------------------------------------ #
    #  Generate                                                             #
    # ------------------------------------------------------------------ #

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 64,
        temperature: float = 0.8,
        top_k: int = 50,
        top_p: float = 1.0,
        repetition_penalty: float = 1.0,
    ) -> str:
        self._assert_loaded()
        assert self.model is not None and self.tokenizer is not None
        ids = self.tokenizer.encode(prompt, add_bos=True)
        ids = ids[-self.model.cfg.max_seq_len:]
        x = torch.tensor([ids], device=self.device)
        out = self.model.generate(
            x,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            eos_token_id=self.tokenizer.eos_id,
        )
        return self.tokenizer.decode(out[0].tolist())

    def generate_stream(
        self,
        prompt: str,
        max_new_tokens: int = 64,
        temperature: float = 0.8,
        top_k: int = 50,
        top_p: float = 1.0,
        repetition_penalty: float = 1.0,
    ) -> Generator[str, None, None]:
        """Yield decoded text chunks one token at a time (best-effort UTF-8)."""
        self._assert_loaded()
        assert self.model is not None and self.tokenizer is not None
        ids = self.tokenizer.encode(prompt, add_bos=True)
        ids = ids[-self.model.cfg.max_seq_len:]
        x = torch.tensor([ids], device=self.device)

        inv_vocab = {v: k for k, v in self.tokenizer.vocab.items()}
        import re

        for token_tensor in self.model.generate_stream(
            x,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            eos_token_id=self.tokenizer.eos_id,
        ):
            token_id = int(token_tensor.view(-1)[0])
            sym = inv_vocab.get(token_id, "")
            raw = bytearray()
            for hx in re.findall(r"<0x([0-9A-F]{2})>", sym):
                raw.append(int(hx, 16))
            if raw:
                yield raw.decode("utf-8", errors="replace")

    # ------------------------------------------------------------------ #
    #  Chat                                                                 #
    # ------------------------------------------------------------------ #

    def chat(self, messages: list[dict], **gen_kwargs) -> str:
        """Run a chat conversation and return the assistant reply as a string.

        Uses ``tokenizer.encode_chat`` when available (chat special tokens
        present), otherwise falls back to a simple text template.
        """
        self._assert_loaded()
        assert self.tokenizer is not None

        if hasattr(self.tokenizer, "encode_chat") and self.tokenizer.inspect().get("chat_tokens_available"):
            # End at opening <assistant> so the model continues the reply —
            # never append <eos> before generation.
            ids = self.tokenizer.encode_chat(messages, add_generation_prompt=True)
            ids = ids[-self.model.cfg.max_seq_len :]  # type: ignore[union-attr]
            x = torch.tensor([ids], device=self.device)
            stop_ids: list[int] = []
            asst_end = self.tokenizer.assistant_end_id
            if asst_end is not None:
                stop_ids.append(asst_end)
            out = self.model.generate(  # type: ignore[union-attr]
                x,
                max_new_tokens=gen_kwargs.get("max_new_tokens", 256),
                temperature=gen_kwargs.get("temperature", 0.8),
                top_k=gen_kwargs.get("top_k", 50),
                top_p=gen_kwargs.get("top_p", 1.0),
                repetition_penalty=gen_kwargs.get("repetition_penalty", 1.0),
                eos_token_id=self.tokenizer.eos_id,
                stop_token_ids=stop_ids or None,
            )
            # Decode only newly generated tokens (skip the chat prompt).
            prompt_len = x.size(1)
            new_ids = out[0, prompt_len:].tolist()
            return self.tokenizer.decode(new_ids)

        # Fallback: simple text formatting
        parts: list[str] = []
        for m in messages:
            role = m.get("role", "user").capitalize()
            parts.append(f"{role}: {m.get('content', '')}")
        parts.append("Assistant:")
        prompt = "\n".join(parts)
        return self.generate(prompt, **gen_kwargs)

    # ------------------------------------------------------------------ #
    #  RAG-augmented generate                                               #
    # ------------------------------------------------------------------ #

    def generate_with_context(
        self,
        prompt: str,
        rag_context: list[str] | None = None,
        memory_snippets: list[str] | None = None,
        **gen_kwargs,
    ) -> str:
        """Generate a response augmented with retrieval context and memory.

        The constructed prompt instructs the model to cite context where
        relevant (best-effort — tiny models may not follow instructions).
        """
        parts: list[str] = []
        if memory_snippets:
            parts.append("## Relevant memory\n" + "\n".join(f"- {s}" for s in memory_snippets))
        if rag_context:
            parts.append(
                "## Retrieved context\n"
                + "\n".join(f"[{i+1}] {s}" for i, s in enumerate(rag_context))
                + "\n\nWhen answering, cite sources as [1], [2], etc. where applicable."
            )
        parts.append(f"## Question\n{prompt}")
        augmented = "\n\n".join(parts)
        return self.generate(augmented, **gen_kwargs)

    # ------------------------------------------------------------------ #
    #  Info                                                                 #
    # ------------------------------------------------------------------ #

    def info(self) -> dict:
        if self.model is None:
            return {"loaded": False}
        assert self.tokenizer is not None
        return {
            "loaded": True,
            "device": str(self.device),
            "parameters": self.model.exact_parameter_count(),
            "vocab_size": len(self.tokenizer.vocab),
            "config_path": self._config_path,
            "checkpoint_path": self._checkpoint_path,
            "tokenizer_info": self.tokenizer.inspect(),
        }
