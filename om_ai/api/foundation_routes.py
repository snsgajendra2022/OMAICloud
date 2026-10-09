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



# ---------------------------------------------------------------------------
# Controlled ML lifecycle APIs
# ---------------------------------------------------------------------------
class MLFeedbackRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=12000)
    answer: str = Field(..., min_length=1, max_length=24000)
    rating: int = Field(..., ge=-1, le=1)
    reason: str = Field("", max_length=2000)
    conversation_id: str = Field("", max_length=200)
    consent_to_training: bool = False


class MLDatasetPrepareRequest(BaseModel):
    records: list[dict[str, Any]] = Field(..., min_length=1, max_length=10000)


class MLEvaluationRequest(BaseModel):
    questions: list[str] = Field(..., min_length=1, max_length=100)
    max_new_tokens: int = Field(128, ge=1, le=1024)


def _tenant_learning_root(tenant_id: str) -> Path:
    import hashlib
    import os

    base = Path(os.getenv("OM_LEARNING_ROOT", "artifacts/learning"))
    tenant_key = hashlib.sha256((tenant_id or "default").encode("utf-8")).hexdigest()[:16]
    return base / "tenants" / tenant_key


@router.get("/api/ml/status")
def ml_status(
    ctx: TenantContext = Depends(require_permission("model.generate")),
) -> dict[str, Any]:
    """Return learning readiness without loading or changing any model weights."""
    import json
    import os

    root = _tenant_learning_root(ctx.tenant_id)
    dataset_dir = root / "datasets"
    manifests = []
    if dataset_dir.is_dir():
        for path in sorted(dataset_dir.glob("*.manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]:
            try:
                manifests.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
    feedback_path = root / "feedback.jsonl"
    feedback_count = 0
    if feedback_path.is_file():
        try:
            with feedback_path.open("r", encoding="utf-8") as handle:
                feedback_count = sum(1 for line in handle if line.strip())
        except OSError:
            pass
    registry_root = Path(os.getenv("OM_AI_REGISTRY", "artifacts/registry"))
    registered = []
    if registry_root.is_dir():
        for metadata_path in registry_root.glob("*/metadata.json"):
            try:
                data = json.loads(metadata_path.read_text(encoding="utf-8"))
                registered.append({
                    "version": data.get("version") or metadata_path.parent.name,
                    "state": data.get("state", "unknown"),
                })
            except (OSError, json.JSONDecodeError):
                continue
    return {
        "ok": True,
        "learning_enabled": os.getenv("OM_LEARNING_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"},
        "auto_promotion_enabled": os.getenv("OM_LEARNING_AUTO_PROMOTION", "false").strip().lower() in {"1", "true", "yes", "on"},
        "training_requires_explicit_enablement": True,
        "production_weights_changed_by_status": False,
        "dataset_versions": manifests,
        "feedback_events": feedback_count,
        "registered_models": registered[:100],
        "active_model_id": os.getenv("OM_MODEL_ID") or os.getenv("OM_AI_MODEL_ID") or "OM-1.0",
    }


@router.post("/api/ml/feedback")
def ml_feedback(
    req: MLFeedbackRequest,
    ctx: TenantContext = Depends(require_auth),
) -> dict[str, Any]:
    """Store feedback as a learning candidate; training consent is opt-in."""
    from om_ai.core.machine_learning.feedback.feedback_collector import FeedbackCollector

    collector = FeedbackCollector(_tenant_learning_root(ctx.tenant_id) / "feedback.jsonl")
    event = collector.add(
        req.question,
        req.answer,
        rating=req.rating,
        reason=req.reason,
        conversation_id=req.conversation_id,
        consent_to_training=req.consent_to_training,
        metadata={"actor": ctx.actor or "", "tenant_scoped": True},
    )
    return {
        "ok": True,
        "event_id": event["event_id"],
        "consent_to_training": event["consent_to_training"],
        "training_started": False,
        "message": "Feedback saved as a candidate signal; it does not change production weights.",
    }


@router.post("/api/ml/datasets/prepare")
def ml_prepare_dataset(
    req: MLDatasetPrepareRequest,
    ctx: TenantContext = Depends(require_permission("admin")),
) -> dict[str, Any]:
    """Validate and content-version a dataset for a future controlled training job."""
    from om_ai.core.machine_learning.data.dataset_manager import DatasetManager
    from om_ai.core.machine_learning.learning_config import LearningConfig
    from om_ai.core.machine_learning.learning_engine import LearningEngine

    root = _tenant_learning_root(ctx.tenant_id)
    config = LearningConfig.from_env()
    config = LearningConfig(
        root=root,
        train_ratio=config.train_ratio,
        validation_ratio=config.validation_ratio,
        test_ratio=config.test_ratio,
        minimum_quality_score=config.minimum_quality_score,
        allow_training=config.allow_training,
        allow_auto_promotion=False,
    )
    engine = LearningEngine(config=config, dataset_manager=DatasetManager(root / "datasets"))
    try:
        result = engine.prepare(req.records)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, **result.to_dict()}


@router.post("/api/ml/evaluate")
def ml_evaluate(
    req: MLEvaluationRequest,
    ctx: TenantContext = Depends(require_permission("admin")),
) -> dict[str, Any]:
    """Run a small, explicit candidate smoke evaluation through ModelGateway."""
    from om_ai.core.machine_learning.evaluation.evaluation_engine import EvaluationEngine
    from om_ai.core.model_runtime.model_gateway import ModelGateway

    gateway = ModelGateway.get_instance()

    def generate(question: str) -> str:
        result = gateway.generate(
            question,
            max_new_tokens=req.max_new_tokens,
            metadata={"purpose": "ml_candidate_evaluation", "tenant_id": ctx.tenant_id},
        )
        if not result.success:
            raise RuntimeError(result.reason or "Model generation failed")
        return result.text

    try:
        metrics = EvaluationEngine().evaluate(
            [{"question": question} for question in req.questions],
            generate,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Model evaluation unavailable: {type(exc).__name__}") from exc
    return {"ok": True, "model_id": "configured-production-gateway", "metrics": metrics, "production_changed": False}
