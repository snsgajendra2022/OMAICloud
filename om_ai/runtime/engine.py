from __future__ import annotations
import codecs
import logging
from typing import Generator
import torch
from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer
from om_ai.tokenizer import load_tokenizer

logger = logging.getLogger(__name__)


class LocalLLMEngine:
    def __init__(self) -> None:
        self.model = None
        self.tokenizer = None
        self.device = None
        self._config_path = None
        self._checkpoint_path = None

    def load(self, config_path: str, tokenizer_path: str, checkpoint_path: str, device: str | None = None) -> dict:
        cfg = ModelConfig.from_json(config_path)
        self.tokenizer = load_tokenizer(tokenizer_path)
        if cfg.vocab_size != len(self.tokenizer.vocab):
            cfg.vocab_size = len(self.tokenizer.vocab)

        ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        state = ckpt.get("model", ckpt)

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

        return {
            "device": str(self.device),
            "parameters": self.model.exact_parameter_count(),
            "tokenizer": self.tokenizer.inspect(),
            "checkpoint": checkpoint_path,
        }

    def _assert_loaded(self):
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model is not loaded. Call load() first.")

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
        ids = self.tokenizer.encode(prompt, add_bos=True)
        ids = ids[-self.model.cfg.max_seq_len:]
        prompt_len = len(ids)
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
        return self.tokenizer.decode(out[0].tolist()[prompt_len:])

    def generate_stream(
        self,
        prompt: str,
        max_new_tokens: int = 64,
        temperature: float = 0.8,
        top_k: int = 50,
        top_p: float = 1.0,
        repetition_penalty: float = 1.0,
    ) -> Generator[str, None, None]:
        self._assert_loaded()
        ids = self.tokenizer.encode(prompt, add_bos=True)
        ids = ids[-self.model.cfg.max_seq_len:]
        x = torch.tensor([ids], device=self.device)
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")

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
            if token_id == self.tokenizer.eos_id:
                break
            raw = self.tokenizer.token_bytes(token_id)
            if not raw:
                continue
            chunk = decoder.decode(raw, final=False)
            if chunk:
                yield chunk

        tail = decoder.decode(b"", final=True)
        if tail:
            yield tail

    def chat(self, messages: list[dict], **gen_kwargs) -> str:
        self._assert_loaded()

        if self.tokenizer.inspect().get("chat_tokens_available"):
            ids = self.tokenizer.encode_chat(
                messages,
                add_generation_prompt=True,
                add_eos=False,
            )
            ids = ids[-self.model.cfg.max_seq_len:]
            prompt_len = len(ids)
            x = torch.tensor([ids], device=self.device)

            stops = []
            if self.tokenizer.assistant_end_id is not None:
                stops.append(self.tokenizer.assistant_end_id)

            out = self.model.generate(
                x,
                max_new_tokens=gen_kwargs.get("max_new_tokens", 256),
                temperature=gen_kwargs.get("temperature", 0.8),
                top_k=gen_kwargs.get("top_k", 50),
                top_p=gen_kwargs.get("top_p", 1.0),
                repetition_penalty=gen_kwargs.get("repetition_penalty", 1.0),
                eos_token_id=self.tokenizer.eos_id,
                stop_token_ids=stops,
            )
            return self.tokenizer.decode(out[0].tolist()[prompt_len:]).strip()

        parts = []
        for m in messages:
            parts.append(f"{m.get('role', 'user').capitalize()}: {m.get('content', '')}")
        parts.append("Assistant:")
        return self.generate("\n".join(parts), **gen_kwargs).strip()

    def generate_with_context(
        self,
        prompt: str,
        rag_context: list[str] | None = None,
        memory_snippets: list[str] | None = None,
        **gen_kwargs,
    ) -> str:
        parts = []
        if memory_snippets:
            parts.append("## Relevant memory\n" + "\n".join(f"- {s}" for s in memory_snippets))
        if rag_context:
            parts.append(
                "## Retrieved context\n"
                + "\n".join(f"[{i+1}] {s}" for i, s in enumerate(rag_context))
            )
        parts.append(f"## Question\n{prompt}")
        return self.generate("\n\n".join(parts), **gen_kwargs)

    def info(self) -> dict:
        if self.model is None:
            return {"loaded": False}
        return {
            "loaded": True,
            "device": str(self.device),
            "parameters": self.model.exact_parameter_count(),
            "vocab_size": len(self.tokenizer.vocab),
            "config_path": self._config_path,
            "checkpoint_path": self._checkpoint_path,
            "tokenizer_info": self.tokenizer.inspect(),
        }
