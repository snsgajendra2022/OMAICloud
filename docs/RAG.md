# RAG (Retrieval-Augmented Generation)

Module: `om_ai/knowledge/rag.py` — `PersistentKnowledgeBase` (and related helpers).

## Design

- Persistent SQLite index, tenant-scoped
- Default embeddings: hashed TF-IDF / bag-of-words over NumPy — **no external AI embed API**
- Chunk → embed → retrieve → optional rerank → context pack
- Document parsers: `.txt`, `.md`, `.json`, `.csv`, `.html`; optional `.pdf` / `.docx` if `pypdf` / `python-docx` installed

Override `embed_text` on a subclass to plug a dense local encoder later.

## Paths

- Default KB: `artifacts/knowledge.sqlite3` (`OM_AI_KB`)
- Agent tool: `om_ai/actions/knowledge.py` (`KnowledgeSearchTool`)

## Honesty

Lexical/TF-IDF RAG helps grounded answers from **your** documents. It does not create a frontier LLM. Retrieval quality depends on chunking, corpus hygiene, and the generator checkpoint.
