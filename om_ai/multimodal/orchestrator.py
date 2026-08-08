"""
OM AI Multimodal Orchestrator.

Routes a ``UnifiedRequest`` (text + images + audio + documents) to the
appropriate processing backend, returning a structured response.

Routing logic:
  - ``documents`` → RAG ingest then retrieve; augment LLM prompt
  - ``images``    → vision encoder (VisionLanguageModel) if available, else error
  - ``audio``     → ASR encoder (CTCAudioEncoder) if available, else error
  - ``text``      → LLM (LocalLLMEngine)

All modalities that are unavailable raise ``ModalityUnavailableError`` with
a clear message rather than silently falling back or fabricating output.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ModalityUnavailableError(Exception):
    """Raised when a required modality encoder is not configured."""


# ─────────────────────────────────────────────────────────────────────────────
# Request / response schema
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class UnifiedRequest:
    """A multimodal request carrying any combination of input modalities."""
    text: str = ""
    images: list[str] = field(default_factory=list)     # file paths
    audio: list[str] = field(default_factory=list)      # file paths
    documents: list[str] = field(default_factory=list)  # file paths or raw text
    max_new_tokens: int = 256
    temperature: float = 0.8


@dataclass
class UnifiedResponse:
    """Structured response from the multimodal orchestrator."""
    text: str
    modalities_used: list[str] = field(default_factory=list)
    rag_sources: list[str] = field(default_factory=list)
    asr_transcripts: list[str] = field(default_factory=list)
    vision_descriptions: list[str] = field(default_factory=list)
    error: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ─────────────────────────────────────────────────────────────────────────────


class UnifiedOrchestrator:
    """Route a UnifiedRequest to the correct processing backends.

    Args:
        llm_engine: A ``LocalLLMEngine`` (or compatible object with
            ``.generate_with_context(prompt, rag_context, **kw)`` and
            ``.generate(prompt, **kw)``).
        knowledge_base: Optional RAG store for document ingestion/retrieval.
            Must support ``.add(doc_id, text, metadata)`` and
            ``.search(query, k)``.
        vision_model: Optional vision-language model with
            ``.describe_image(path) -> str``.
        asr_model: Optional ASR model with
            ``.transcribe(path) -> str``.
    """

    def __init__(
        self,
        llm_engine: Any | None = None,
        knowledge_base: Any | None = None,
        vision_model: Any | None = None,
        asr_model: Any | None = None,
    ) -> None:
        self._llm = llm_engine
        self._kb = knowledge_base
        self._vision = vision_model
        self._asr = asr_model

    # ------------------------------------------------------------------ #
    #  Public interface                                                     #
    # ------------------------------------------------------------------ #

    def run(
        self,
        text: str = "",
        images: list[str] | None = None,
        audio: list[str] | None = None,
        documents: list[str] | None = None,
        max_new_tokens: int = 256,
        temperature: float = 0.8,
    ) -> dict:
        """Convenience wrapper that accepts keyword arguments directly.

        Returns a plain dict matching ``UnifiedResponse`` structure.
        """
        req = UnifiedRequest(
            text=text,
            images=images or [],
            audio=audio or [],
            documents=documents or [],
            max_new_tokens=max_new_tokens,
            temperature=temperature,
        )
        resp = self.process(req)
        return {
            "text": resp.text,
            "modalities_used": resp.modalities_used,
            "rag_sources": resp.rag_sources,
            "asr_transcripts": resp.asr_transcripts,
            "vision_descriptions": resp.vision_descriptions,
            "error": resp.error,
        }

    def process(self, req: UnifiedRequest) -> UnifiedResponse:
        """Process a UnifiedRequest and return a UnifiedResponse."""
        modalities_used: list[str] = []
        rag_context: list[str] = []
        rag_sources: list[str] = []
        asr_transcripts: list[str] = []
        vision_descriptions: list[str] = []
        extra_text_parts: list[str] = []

        # ── 1. Documents → RAG ingest + retrieve ──────────────────────
        if req.documents:
            doc_results = self._handle_documents(req.documents, req.text)
            rag_context = doc_results["snippets"]
            rag_sources = doc_results["sources"]
            if rag_context:
                modalities_used.append("document")

        # ── 2. Images → vision encoder ────────────────────────────────
        if req.images:
            desc_list = self._handle_images(req.images)
            vision_descriptions = desc_list
            extra_text_parts.extend(f"[Image description: {d}]" for d in desc_list)
            modalities_used.append("image")

        # ── 3. Audio → ASR ────────────────────────────────────────────
        if req.audio:
            transcripts = self._handle_audio(req.audio)
            asr_transcripts = transcripts
            extra_text_parts.extend(f"[Audio transcript: {t}]" for t in transcripts)
            modalities_used.append("audio")

        # ── 4. Build final text prompt ────────────────────────────────
        prompt_parts = []
        if extra_text_parts:
            prompt_parts.append("\n".join(extra_text_parts))
        if req.text:
            prompt_parts.append(req.text)
        prompt = "\n\n".join(prompt_parts) if prompt_parts else req.text
        modalities_used.append("text")

        # ── 5. LLM generation ─────────────────────────────────────────
        if self._llm is None:
            return UnifiedResponse(
                text="",
                modalities_used=modalities_used,
                rag_sources=rag_sources,
                asr_transcripts=asr_transcripts,
                vision_descriptions=vision_descriptions,
                error="No LLM engine configured.",
            )

        try:
            if rag_context and hasattr(self._llm, "generate_with_context"):
                output = self._llm.generate_with_context(
                    prompt,
                    rag_context=rag_context,
                    max_new_tokens=req.max_new_tokens,
                    temperature=req.temperature,
                )
            else:
                output = self._llm.generate(
                    prompt,
                    max_new_tokens=req.max_new_tokens,
                    temperature=req.temperature,
                )
        except Exception as exc:
            logger.error("LLM generation failed: %s", exc)
            return UnifiedResponse(
                text="",
                modalities_used=modalities_used,
                rag_sources=rag_sources,
                asr_transcripts=asr_transcripts,
                vision_descriptions=vision_descriptions,
                error=str(exc),
            )

        return UnifiedResponse(
            text=output,
            modalities_used=modalities_used,
            rag_sources=rag_sources,
            asr_transcripts=asr_transcripts,
            vision_descriptions=vision_descriptions,
        )

    # ------------------------------------------------------------------ #
    #  Modality handlers                                                    #
    # ------------------------------------------------------------------ #

    def _handle_documents(self, paths_or_texts: list[str], query: str) -> dict:
        """Ingest documents into the knowledge base and retrieve relevant chunks."""
        if self._kb is None:
            raise ModalityUnavailableError(
                "Document modality requires a knowledge base (knowledge_base=...). "
                "Configure a PersistentKnowledgeBase and pass it to UnifiedOrchestrator."
            )
        import uuid as _uuid

        sources: list[str] = []
        for item in paths_or_texts:
            doc_id = _uuid.uuid4().hex
            if len(item) < 4096 and Path(item).exists():
                try:
                    text = Path(item).read_text(encoding="utf-8", errors="replace")
                    sources.append(item)
                except Exception as exc:
                    logger.warning("Could not read document %s: %s", item, exc)
                    continue
            else:
                text = item
                sources.append(f"inline:{doc_id[:8]}")
            try:
                self._kb.add(doc_id, text, {"source": sources[-1]})
            except Exception as exc:
                logger.warning("Failed to ingest document: %s", exc)

        # Retrieve relevant chunks for the query
        snippets: list[str] = []
        if query:
            try:
                results = self._kb.search(query, k=5)
                for r in results:
                    if isinstance(r, dict):
                        snippets.append(r.get("text") or r.get("content") or str(r))
                    elif hasattr(r, "text"):
                        snippets.append(r.text)
                    else:
                        snippets.append(str(r))
            except Exception as exc:
                logger.warning("Knowledge base search failed: %s", exc)

        return {"snippets": snippets, "sources": sources}

    def _handle_images(self, image_paths: list[str]) -> list[str]:
        """Describe images using the vision encoder."""
        if self._vision is None:
            # Attempt to lazily load the built-in vision model
            try:
                from om_ai.vision.multimodal import VisionLanguageModel
                self._vision = VisionLanguageModel()
            except Exception:
                raise ModalityUnavailableError(
                    "Image modality requires a vision encoder. "
                    "Install vision extras (pip install om-ai-operating-brain[vision]) "
                    "and configure a vision model."
                )

        descriptions: list[str] = []
        for path in image_paths:
            if not Path(path).exists():
                descriptions.append(f"[Image not found: {path}]")
                continue
            try:
                if hasattr(self._vision, "describe_image"):
                    desc = self._vision.describe_image(path)
                else:
                    desc = f"[Vision model does not support describe_image: {path}]"
                descriptions.append(str(desc))
            except Exception as exc:
                logger.warning("Vision inference failed for %s: %s", path, exc)
                descriptions.append(f"[Vision error: {exc}]")

        return descriptions

    def _handle_audio(self, audio_paths: list[str]) -> list[str]:
        """Transcribe audio using the ASR encoder."""
        if self._asr is None:
            try:
                from om_ai.voice.audio_encoder import CTCAudioEncoder
                self._asr = CTCAudioEncoder()
            except Exception:
                raise ModalityUnavailableError(
                    "Audio modality requires an ASR encoder. "
                    "Install voice extras and configure an audio encoder."
                )

        transcripts: list[str] = []
        for path in audio_paths:
            if not Path(path).exists():
                transcripts.append(f"[Audio not found: {path}]")
                continue
            try:
                if hasattr(self._asr, "transcribe"):
                    text = self._asr.transcribe(path)
                else:
                    text = f"[ASR model does not support transcribe: {path}]"
                transcripts.append(str(text))
            except Exception as exc:
                logger.warning("ASR failed for %s: %s", path, exc)
                transcripts.append(f"[ASR error: {exc}]")

        return transcripts
