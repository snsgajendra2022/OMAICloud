"""Foundation APIs: knowledge, reasoning, evaluation, learning."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from om_ai.api.deps import require_auth, require_permission
from om_ai.security.auth import TenantContext

router = APIRouter(tags=["Foundation"])


class ReasonRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=20000)
    use_knowledge: bool = True
    k: int = Field(5, ge=1, le=20)


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    k: int = Field(5, ge=1, le=20)


class UploadPathRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=1000)
    domain: str = ""


class FeedbackRequest(BaseModel):
    problem: str = Field(..., min_length=1, max_length=8000)
    old_answer: str = Field("", max_length=20000)
    correct_answer: str = Field(..., min_length=1, max_length=20000)
    rating: int = Field(2, ge=1, le=5)


class EvalRequest(BaseModel):
    out: str = "artifacts/eval/foundation_report.json"


@router.post("/api/knowledge/search")
def knowledge_search(
    req: SearchRequest,
    ctx: TenantContext = Depends(require_permission("knowledge.read")),
) -> dict[str, Any]:
    from om_ai.knowledge.retrieval import search_knowledge

    hits = search_knowledge(req.query, tenant_id=ctx.tenant_id, k=req.k)
    return {"query": req.query, "hits": hits, "count": len(hits)}


@router.post("/api/knowledge/upload")
def knowledge_upload(
    req: UploadPathRequest,
    ctx: TenantContext = Depends(require_permission("knowledge.write")),
) -> dict[str, Any]:
    """Ingest a server-local file path into the knowledge engine."""
    from om_ai.knowledge.retrieval import upload_document

    path = Path(req.path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {req.path}")
    try:
        result = upload_document(str(path), tenant_id=ctx.tenant_id, domain=req.domain or None)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "path": str(path), **result}


@router.post("/api/reasoning/analyze")
def reasoning_analyze(
    req: ReasonRequest,
    ctx: TenantContext = Depends(require_permission("model.generate")),
) -> dict[str, Any]:
    from om_ai.core.reasoning import run_reasoning_pipeline
    from om_ai.knowledge.retrieval import search_knowledge

    hits: list[str] = []
    if req.use_knowledge:
        for h in search_knowledge(req.question, tenant_id=ctx.tenant_id, k=req.k):
            hits.append(str(h.get("text") or ""))
    return run_reasoning_pipeline(req.question, knowledge_hits=hits)


@router.post("/api/evaluation/run")
def evaluation_run(
    req: EvalRequest | None = None,
    ctx: TenantContext = Depends(require_permission("model.generate")),
) -> dict[str, Any]:
    from om_ai.evaluation import run_evaluation

    out = (req.out if req else None) or "artifacts/eval/foundation_report.json"
    return run_evaluation(out=out)


@router.post("/api/learning/feedback")
def learning_feedback(
    req: FeedbackRequest,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    from om_ai.learning import record_feedback

    return record_feedback(
        problem=req.problem,
        old_answer=req.old_answer,
        correct_answer=req.correct_answer,
        rating=req.rating,
        user_id=ctx.actor or "",
    )


@router.post("/api/learning/export")
def learning_export(
    ctx: TenantContext = Depends(require_permission("admin")),
) -> dict[str, Any]:
    from om_ai.learning import build_datasets

    return build_datasets()
