from __future__ import annotations
import codecs
import logging
import re
from pathlib import Path
from typing import Any, Generator
import torch
from om_ai.core import config
from om_ai.core.config import ModelConfig
from om_ai.model import OMTransformer
from om_ai.tokenizer import load_tokenizer, tokenizer_fingerprint
from om_ai.tokenizer.byte_bpe import ByteBPETokenizer

logger = logging.getLogger(__name__)

EMPTY_GENERATION_FALLBACK = "OM-1.0 produced no text; try again."
_CTRL_OR_REPLACEMENT = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\uFFFD]")


class CheckpointTokenizerMismatch(ValueError):
    """Checkpoint was bound to a different tokenizer fingerprint or vocab size."""


_KNOWN_TOKENIZERS = (
    "artifacts/tokenizer-production-65536.json",
    "artifacts/tokenizer-fixed-v3.json",
    "artifacts/tokenizer-om-production.json",
    "artifacts/tokenizer.json",
)


def validate_model_tokenizer(model, tokenizer) -> None:
        """
        Validate that the loaded model and tokenizer use the same vocabulary.

        This must run immediately after both objects are loaded and before
        model generation starts.
        """

        model_vocab = None
        tokenizer_vocab = None

        # ---------------------------------------------------------
        # Model vocabulary
        # ---------------------------------------------------------

        if hasattr(model, "config"):
            model_vocab = getattr(
                model.config,
                "vocab_size",
                None,
            )

        if hasattr(model, "vocab_size"):
            model_vocab = getattr(
                model,
                "vocab_size",
                model_vocab,
            )

        # ---------------------------------------------------------
        # Tokenizer vocabulary
        # ---------------------------------------------------------

        if hasattr(tokenizer, "vocab_size"):
            tokenizer_vocab = tokenizer.vocab_size

        # Some custom tokenizers expose the vocabulary through
        # get_vocab() instead of vocab_size.
        if tokenizer_vocab is None:
            get_vocab = getattr(
                tokenizer,
                "get_vocab",
                None,
            )

            if callable(get_vocab):
                try:
                    vocab = get_vocab()

                    if vocab:
                        tokenizer_vocab = len(vocab)

                except Exception:
                    tokenizer_vocab = None

        # ---------------------------------------------------------
        # Validate
        # ---------------------------------------------------------

        if (
            model_vocab is not None
            and tokenizer_vocab is not None
        ):
            if int(model_vocab) != int(tokenizer_vocab):
                raise RuntimeError(
                    "MODEL/TOKENIZER VOCAB MISMATCH: "
                    f"model={model_vocab}, "
                    f"tokenizer={tokenizer_vocab}"
                )

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _embedding_vocab(state: Any) -> int | None:
    if not isinstance(state, dict):
        return None
    for key, value in state.items():
        name = str(key)
        if name == "token_embedding.weight" or name.endswith(".token_embedding.weight"):
            try:
                return int(value.shape[0])
            except Exception:
                return None
    return None


def resolve_tokenizer_path_for_checkpoint(
    tokenizer_path: str,
    ckpt_vocab: int | None,
    extra: dict | None = None,
) -> str:
    """Return a tokenizer whose vocab size matches checkpoint embeddings.

    Stale checkpoint metadata can claim tokenizer-fixed-v3 while the weights
    were actually trained at 65536. Prefer the requested path when it matches;
    otherwise search extra.tokenizer_path and known artifacts.
    """
    requested = Path(tokenizer_path)
    tok_n = len(load_tokenizer(requested).vocab)
    if ckpt_vocab is None or tok_n == ckpt_vocab:
        return str(requested)

    candidates: list[Path] = []
    if isinstance(extra, dict):
        raw = extra.get("tokenizer_path")
        if raw:
            p = Path(str(raw))
            candidates.append(p)
            if not p.is_absolute():
                candidates.append(_repo_root() / p)
    for rel in _KNOWN_TOKENIZERS:
        candidates.append(_repo_root() / rel)

    seen: set[str] = set()
    try:
        seen.add(str(requested.resolve()))
    except OSError:
        seen.add(str(requested))

    for cand in candidates:
        if not cand.is_file():
            continue
        try:
            key = str(cand.resolve())
        except OSError:
            key = str(cand)
        if key in seen:
            continue
        seen.add(key)
        try:
            n = len(load_tokenizer(cand).vocab)
        except Exception:
            continue
        if n == ckpt_vocab:
            logger.warning(
                "Checkpoint embeddings are vocab=%s but tokenizer %s has vocab=%s; "
                "using matching tokenizer %s",
                ckpt_vocab,
                tokenizer_path,
                tok_n,
                cand,
            )
            return str(cand)

    raise CheckpointTokenizerMismatch(
        f"Checkpoint embedding vocab is {ckpt_vocab} but tokenizer {tokenizer_path} "
        f"has vocab {tok_n}. Set OM_MODEL_TOKENIZER to a matching file "
        f"(artifacts/tokenizer-production-65536.json for 65536, "
        f"artifacts/tokenizer-fixed-v3.json for ~340)."
    )


def _extra_tokenizer_matches_vocab(extra: dict | None, ckpt_vocab: int | None) -> bool:
    if not isinstance(extra, dict) or not extra.get("tokenizer_path") or ckpt_vocab is None:
        return True
    p = Path(str(extra["tokenizer_path"]))
    if not p.is_file():
        p = _repo_root() / p
    if not p.is_file():
        return True
    try:
        return len(load_tokenizer(p).vocab) == ckpt_vocab
    except Exception:
        return True


def usable_generation_text(text: str | None) -> str:
    """Return stripped text if it looks like a real reply; else empty string."""
    s = (text or "").strip()
    if not s:
        return ""
    # Reject control bytes / replacement-char garbage from broken prompts.
    cleaned = _CTRL_OR_REPLACEMENT.sub("", s).strip()
    if not cleaned:
        return ""
    printable = sum(1 for c in cleaned if c.isprintable() or c in "\n\t")
    if printable < max(1, int(0.7 * len(cleaned))):
        return ""
    return cleaned


def is_degenerate_generation(text: str | None) -> bool:
    """True when local OM-1.0 collapsed into repeated possessives / token soup."""
    s = (text or "").strip()
    if not s:
        return True
    if not usable_generation_text(s):
        return True
    words = re.findall(r"\S+", s)
    if len(words) < 12:
        return False
    poss = sum(1 for w in words if "'s" in w or "’s" in w)
    if poss / len(words) >= 0.18:
        return True
    uniq = len({re.sub(r"[^\w]+", "", w.lower()) for w in words} - {""})
    if uniq / len(words) < 0.22:
        return True
    return False


def fit_messages_to_context(
    messages: list[dict],
    tokenizer,
    max_seq_len: int,
    *,
    today=None,
) -> list[dict]:
    """Shrink chat messages so encode_chat(+generation prompt) fits max_seq_len.

    Priority: keep the latest user turn and ``<assistant>`` open tag intact.
    Long system preambles are compacted or dropped first (critical for
    max_seq_len=128 local checkpoints).
    """
    max_seq_len = max(8, int(max_seq_len))

    def _enc(msgs: list[dict]) -> list[int]:
        return tokenizer.encode_chat(msgs, add_generation_prompt=True, add_eos=False)

    msgs = [{"role": str(m.get("role", "user")), "content": str(m.get("content", ""))} for m in messages]
    if len(_enc(msgs)) <= max_seq_len:
        return msgs

    rest = [m for m in msgs if m["role"] != "system"]
    if not rest:
        rest = [{"role": "user", "content": ""}]

    # Drop / compact system. Tiny local windows (e.g. 128) should prefer
    # user+assistant only — SFT greetings were trained that way, and stuffing
    # even a compact system leaves almost no room for a coherent user turn.
    if len(_enc(rest)) <= max_seq_len:
        if max_seq_len > 192:
            try:
                from om_ai.runtime.chat_backend import runtime_date_system_text_compact

                compact = {
                    "role": "system",
                    "content": runtime_date_system_text_compact(today=today),
                }
                candidate = [compact] + rest
                if len(_enc(candidate)) <= max_seq_len:
                    return candidate
            except Exception:
                pass
        return rest

    while len(rest) > 1 and len(_enc(rest)) > max_seq_len:
        rest = rest[1:]
    if len(_enc(rest)) <= max_seq_len:
        return rest

    # Last resort: truncate the final user content.
    last = dict(rest[-1])
    content = last.get("content", "")
    lo, hi = 0, len(content)
    best = ""
    while lo <= hi:
        mid = (lo + hi) // 2
        trial = content[:mid]
        trial_msgs = rest[:-1] + [{"role": last["role"], "content": trial}]
        if len(_enc(trial_msgs)) <= max_seq_len:
            best = trial
            lo = mid + 1
        else:
            hi = mid - 1
    return rest[:-1] + [{"role": last["role"], "content": best}]


class LocalLLMEngine:
    def __init__(self) -> None:
        self.model = None
        self.tokenizer = None
        self.device = None
        self._config_path = None
        self._checkpoint_path = None
        self._tokenizer_path = None
        self._tokenizer_fingerprint = None

    def load(self, config_path: str, tokenizer_path: str, checkpoint_path: str, device: str | None = None) -> dict:
        cfg = ModelConfig.from_json(config_path)
        ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        state = ckpt.get("model", ckpt)
        extra = ckpt.get("extra") if isinstance(ckpt, dict) else None
        ckpt_vocab = _embedding_vocab(state)
        requested_tokenizer = tokenizer_path
        tokenizer_path = resolve_tokenizer_path_for_checkpoint(
            tokenizer_path, ckpt_vocab, extra if isinstance(extra, dict) else None
        )
        switched_tokenizer = Path(tokenizer_path).resolve() != Path(requested_tokenizer).resolve()
        self.tokenizer = load_tokenizer(tokenizer_path)
        tok_fp = tokenizer_fingerprint(tokenizer_path)
        tok_n = len(self.tokenizer.vocab)
        cfg.vocab_size = ckpt_vocab if ckpt_vocab is not None else tok_n

        bound_fp = None
        if isinstance(extra, dict):
            bound_fp = extra.get("tokenizer_fingerprint") or extra.get("tokenizer_sha256")
        if bound_fp and bound_fp != tok_fp:
            stale_meta = switched_tokenizer or not _extra_tokenizer_matches_vocab(
                extra if isinstance(extra, dict) else None, ckpt_vocab
            )
            if stale_meta:
                logger.warning(
                    "Ignoring stale checkpoint tokenizer fingerprint %s "
                    "(using tokenizer %s for embedding vocab=%s)",
                    bound_fp,
                    tokenizer_path,
                    ckpt_vocab,
                )
            else:
                raise CheckpointTokenizerMismatch(
                    f"Checkpoint tokenizer mismatch: checkpoint bound to {bound_fp}, "
                    f"but loaded tokenizer fingerprint is {tok_fp}"
                )

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
        self.tokenizer = ByteBPETokenizer.from_file(
            tokenizer_path
        )
        self.model = OMTransformer(
            config
        ).to(self.device)

        validate_model_tokenizer(
            self.model,
            self.tokenizer,
        )
        missing, unexpected = self.model.load_state_dict(state, strict=False)
        if missing:
            logger.warning("Checkpoint missing keys (non-fatal): %s", missing[:8])
        if unexpected:
            logger.warning("Checkpoint unexpected keys (non-fatal): %s", unexpected[:8])

        self.model.eval()
        self._config_path = config_path
        self._checkpoint_path = checkpoint_path
        self._tokenizer_path = tokenizer_path
        self._tokenizer_fingerprint = tok_fp

        return {
            "device": str(self.device),
            "parameters": self.model.exact_parameter_count(),
            "tokenizer": self.tokenizer.inspect(),
            "tokenizer_fingerprint": tok_fp,
            "checkpoint": checkpoint_path,
        }

    def _assert_loaded(self):
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model is not loaded. Call load() first.")

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 64,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.2,
        min_new_tokens: int = 0,
        no_repeat_ngram_size: int = 3,
        repetition_window: int = 128,
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
            min_new_tokens=min_new_tokens,
            no_repeat_ngram_size=no_repeat_ngram_size,
            repetition_window=repetition_window,
        )
        return self.tokenizer.decode(out[0].tolist()[prompt_len:])

    def generate_stream(
        self,
        prompt: str,
        max_new_tokens: int = 64,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.2,
        min_new_tokens: int = 0,
        no_repeat_ngram_size: int = 3,
        repetition_window: int = 128,
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
            min_new_tokens=min_new_tokens,
            no_repeat_ngram_size=no_repeat_ngram_size,
            repetition_window=repetition_window,
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

    def _chat_once(
        self,
        messages: list[dict],
        *,
        max_new_tokens: int,
        temperature: float,
        top_k: int,
        top_p: float,
        repetition_penalty: float,
        min_new_tokens: int,
        no_repeat_ngram_size: int = 3,
        repetition_window: int = 128,
    ) -> str:
        fitted = fit_messages_to_context(
            messages,
            self.tokenizer,
            self.model.cfg.max_seq_len,
        )
        ids = self.tokenizer.encode_chat(
            fitted,
            add_generation_prompt=True,
            add_eos=False,
        )
        ids = ids[-self.model.cfg.max_seq_len :]
        prompt_len = len(ids)
        x = torch.tensor([ids], device=self.device)

        stops = []
        if self.tokenizer.assistant_end_id is not None:
            stops.append(self.tokenizer.assistant_end_id)

        out = self.model.generate(
            x,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            eos_token_id=self.tokenizer.eos_id,
            stop_token_ids=stops,
            min_new_tokens=min_new_tokens,
            no_repeat_ngram_size=no_repeat_ngram_size,
            repetition_window=repetition_window,
        )
        # Decode only newly generated tokens (specials → empty bytes).
        new_ids = out[0].tolist()[prompt_len:]
        # Drop trailing stop/eos so they never affect strip edge-cases.
        stop_set = set(stops)
        stop_set.add(int(self.tokenizer.eos_id))
        while new_ids and int(new_ids[-1]) in stop_set:
            new_ids.pop()
        return usable_generation_text(self.tokenizer.decode(new_ids))

    def chat(self, messages: list[dict], **gen_kwargs) -> str:
        self._assert_loaded()

        if self.tokenizer.inspect().get("chat_tokens_available"):
            max_new = int(gen_kwargs.get("max_new_tokens", 256))
            temperature = float(gen_kwargs.get("temperature", 0.7))
            top_k = int(gen_kwargs.get("top_k", 50))
            top_p = float(gen_kwargs.get("top_p", 0.9))
            repetition_penalty = float(gen_kwargs.get("repetition_penalty", 1.2))
            min_new = int(gen_kwargs.get("min_new_tokens", 4))
            no_repeat = int(gen_kwargs.get("no_repeat_ngram_size", 3))
            rep_window = int(gen_kwargs.get("repetition_window", 128))

            text = self._chat_once(
                messages,
                max_new_tokens=max_new,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
                min_new_tokens=min_new,
                no_repeat_ngram_size=no_repeat,
                repetition_window=rep_window,
            )
            if text:
                return text

            # Retry once with safer sampling if the first draw was empty/EOS/garbage.
            logger.info("Empty OM chat generation; retrying with temp=0.7 and more tokens")
            text = self._chat_once(
                messages,
                max_new_tokens=max(max_new, 128),
                temperature=0.7,
                top_k=top_k,
                top_p=0.9,
                repetition_penalty=max(repetition_penalty, 1.2),
                min_new_tokens=max(min_new, 8),
                no_repeat_ngram_size=max(no_repeat, 3),
                repetition_window=rep_window,
            )
            if text:
                return text
            return EMPTY_GENERATION_FALLBACK

        parts = []
        for m in messages:
            parts.append(f"{m.get('role', 'user').capitalize()}: {m.get('content', '')}")
        parts.append("Assistant:")
        text = usable_generation_text(self.generate("\n".join(parts), **gen_kwargs))
        return text or EMPTY_GENERATION_FALLBACK

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
            "tokenizer_path": self._tokenizer_path,
            "tokenizer_fingerprint": self._tokenizer_fingerprint,
            "tokenizer_info": self.tokenizer.inspect(),
        }
