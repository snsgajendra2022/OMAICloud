# IMPLEMENTATION_ROADMAP.md

## This pass (implemented and tested)

1. Entity/meaning (PM + India); typo `dahsbaord`.
2. Coding kinds: React login page (frontend), Python API project (backend).
3. Knowledge: `EmbeddingIndex` (vector + metadata) used by retrieval; fact lookup for high-precision Q&A.
4. Reasoning: confidence on pipeline output.
5. Evaluation: relevance, correctness, intent-answered, missing, confidence.
6. Tests in `tests/test_os_validation.py` — features are not marked complete until those tests pass.

## Next

1. Optional dense encoder behind `PersistentKnowledgeBase.embed_text` when a local model is configured (still no cloud embed API by default).
2. Auto knowledge-graph triples from ingested chunks.
3. Allow-listed test runner in CodingAgent (not dry-run only).
4. Conversation summarization into experience memory.

## Later (weights, not this repo checkout)

Train OM-7B/70B on licensed data. Do not mark “5-level trained weights” complete until checkpoints exist and eval suite passes against them.

## Never on the roadmap as product claims

- Human consciousness
- Infinite knowledge without data
