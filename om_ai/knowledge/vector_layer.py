"""
OM-1.0 Vector Knowledge Layer

Production RAG knowledge layer.

Features:

- PersistentKnowledgeBase integration
- Embedding search
- Metadata filtering
- Domain filtering
- Technology filtering
- Quality scoring
- Hybrid ranking
- Duplicate removal
- Top-K retrieval

Flow:

Document
    |
    ↓
Persistent KB
    |
    ↓
Embedding Index
    |
    ↓
Metadata Filter
    |
    ↓
Hybrid Ranking
    |
    ↓
Top Knowledge
"""


from __future__ import annotations


from pathlib import Path

from typing import Any


from om_ai.knowledge.ingestion import ingest_file

from om_ai.knowledge.rag import PersistentKnowledgeBase





class VectorKnowledgeLayer:


    def __init__(
        self,
        *,
        tenant_id: str = "default",
        corpus_root: str | Path | None = None
    ) -> None:


        self.tenant_id = tenant_id

        self.kb = PersistentKnowledgeBase()

        self.corpus_root = Path(
            corpus_root
            or "data/om-knowledge-universe-v1/knowledge"
        )



    # -------------------------------------------------
    # Metadata Filtering
    # -------------------------------------------------

    def _match_metadata(
        self,
        metadata: dict[str, Any] | None,
        filters: dict[str, Any] | None
    ) -> bool:


        if not filters:

            return True


        metadata = metadata or {}


        for key, value in filters.items():


            if value is None:

                continue


            stored = str(
                metadata.get(
                    key,
                    ""
                )
            ).lower()


            expected = str(
                value
            ).lower()



            if expected not in stored:

                return False


        return True



    # -------------------------------------------------
    # Quality Scoring
    # -------------------------------------------------

    def _quality_score(
        self,
        metadata: dict[str, Any]
    ) -> float:


        try:

            return float(
                metadata.get(
                    "quality_score",
                    0.5
                )
            )


        except Exception:

            return 0.5



    # -------------------------------------------------
    # Keyword Score
    # -------------------------------------------------

    def _keyword_score(
        self,
        query: str,
        text: str
    ) -> float:


        q = set(
            query.lower().split()
        )


        t = set(
            text.lower().split()
        )


        if not q:

            return 0.0


        return len(
            q.intersection(t)
        ) / len(q)



    # -------------------------------------------------
    # Hybrid Ranking
    # -------------------------------------------------

    def _hybrid_score(
        self,
        query: str,
        text: str,
        vector_score: float,
        metadata: dict[str, Any]
    ) -> float:



        keyword = self._keyword_score(
            query,
            text
        )


        quality = self._quality_score(
            metadata
        )



        score = (

            vector_score * 0.55

            +

            keyword * 0.25

            +

            quality * 0.20

        )


        return round(
            score,
            4
        )



    # -------------------------------------------------
    # Upload Document
    # -------------------------------------------------

    def upload_path(
        self,
        path: str | Path,
        *,
        domain: str | None = None,
        technology: str | None = None
    ) -> dict[str, Any]:


        path = Path(path)


        run_root = Path(
            "data/om-foundation-corpus"
        )


        info = ingest_file(
            path,
            out_root=run_root
        )


        metadata = dict(
            info["metadata"]
        )


        if domain:

            metadata["domain"] = domain


        if technology:

            metadata["technology"] = technology



        doc_id = self.kb.ingest_file(
            path,
            self.tenant_id,
            metadata=metadata
        )



        try:

            from om_ai.knowledge.embeddings import EmbeddingIndex


            body = path.read_text(
                encoding="utf-8",
                errors="ignore"
            )[:8000]


            EmbeddingIndex().upsert(

                body,

                tenant_id=self.tenant_id,

                metadata=metadata,

                doc_id=str(doc_id)

            )


        except Exception:

            pass



        return {

            "doc_id": doc_id,

            "metadata": metadata,

            "ingestion": info

        }



    # -------------------------------------------------
    # Search Knowledge
    # -------------------------------------------------

    def search(
        self,
        query: str,
        *,
        k: int = 5,
        filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:


        results = []


        seen = set()



        # ---------------------------------------------
        # Persistent Knowledge Base Search
        # ---------------------------------------------

        try:

            hits = self.kb.search(

                query,

                self.tenant_id,

                k=k

            )


            for item in hits or []:


                if hasattr(
                    item,
                    "text"
                ):

                    text = str(
                        item.text
                    )


                    metadata = getattr(
                        item,
                        "metadata",
                        {}
                    ) or {}


                    vector_score = float(
                        getattr(
                            item,
                            "score",
                            0
                        )
                        or 0
                    )


                elif isinstance(
                    item,
                    dict
                ):


                    text = str(
                        item.get(
                            "text",
                            ""
                        )
                    )


                    metadata = item.get(
                        "metadata",
                        {}
                    )


                    vector_score = float(
                        item.get(
                            "score",
                            0
                        )
                        or 0
                    )


                else:

                    continue



                if not text:

                    continue



                if not self._match_metadata(
                    metadata,
                    filters
                ):

                    continue



                final_score = self._hybrid_score(

                    query,

                    text,

                    vector_score,

                    metadata

                )



                key = text[:120]


                if key in seen:

                    continue



                seen.add(key)



                results.append({

                    "text": text[:500],

                    "score": final_score,

                    "metadata": metadata,

                    "source": "persistent_kb"

                })


        except Exception:

            pass




        # ---------------------------------------------
        # Embedding Index Search
        # ---------------------------------------------


        try:

            from om_ai.knowledge.embeddings import EmbeddingIndex


            vector_results = EmbeddingIndex().search(

                query,

                tenant_id=self.tenant_id,

                k=k

            )



            for row in vector_results:


                text = str(
                    row.get(
                        "text",
                        ""
                    )
                )


                metadata = row.get(
                    "metadata",
                    {}
                ) or {}



                if not text:

                    continue



                if not self._match_metadata(
                    metadata,
                    filters
                ):

                    continue



                if text[:120] in seen:

                    continue



                score = self._hybrid_score(

                    query,

                    text,

                    float(
                        row.get(
                            "score",
                            0
                        )
                        or 0
                    ),

                    metadata

                )



                seen.add(
                    text[:120]
                )



                results.append({

                    "text": text[:500],

                    "score": score,

                    "metadata": metadata,

                    "source": "embedding"

                })


        except Exception:

            pass



        results.sort(

            key=lambda x:x["score"],

            reverse=True

        )


        return results[:k]





# -------------------------------------------------
# Public Helpers
# -------------------------------------------------


def search_knowledge(
    query: str,
    *,
    tenant_id: str = "default",
    k: int = 5,
    filters: dict[str, Any] | None = None
):


    return VectorKnowledgeLayer(
        tenant_id=tenant_id
    ).search(

        query,

        k=k,

        filters=filters

    )





def upload_document(
    path: str,
    *,
    tenant_id: str = "default",
    domain: str | None = None,
    technology: str | None = None
):


    return VectorKnowledgeLayer(
        tenant_id=tenant_id
    ).upload_path(

        path,

        domain=domain,

        technology=technology

    )