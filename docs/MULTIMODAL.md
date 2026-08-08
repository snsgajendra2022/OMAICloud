# Multimodal

Router: `om_ai/multimodal/orchestrator.py` (`MultimodalOrchestrator`, `UnifiedRequest` / `UnifiedResponse`).

Vision-language stack: `om_ai/vision/multimodal.py` (`OMVisionLanguageModel`, `MultimodalProjector`).

## Routing

| Input | Path |
|-------|------|
| `documents` | RAG ingest/retrieve (`om_ai/knowledge/`) then augment text prompt |
| `images` | Vision encoder + projector + LLM cross-attention if configured |
| `audio` | ASR encoder path if configured |
| `text` | `LocalLLMEngine` |

Unavailable modalities raise `ModalityUnavailableError` rather than inventing output.

## Requirements for useful multimodal behavior

- LLM config with `cross_attention=true` when using `OMVisionLanguageModel`
- Trained (or at least jointly trained) vision/ASR weights — **not shipped** as production VLM/ASR
- Optional extras: `pip install -e '.[vision]'` / `'.[voice]'`

## Honesty

Software routes and trains foundations. There is no claim of GPT-4V-class vision or Whisper-class ASR from the default package alone. See `VISION.md` and `SPEECH.md`.
