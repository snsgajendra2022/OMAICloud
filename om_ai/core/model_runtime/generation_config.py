from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class GenerationConfig:
    max_new_tokens: int = 256
    temperature: float = 0.35
    top_p: float = 0.90
    repetition_penalty: float = 1.05
    do_sample: bool = True
    min_new_tokens: int = 1

    def to_kwargs(self) -> dict:
        return {
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "repetition_penalty": self.repetition_penalty,
            "do_sample": self.do_sample,
            "min_new_tokens": self.min_new_tokens,
        }