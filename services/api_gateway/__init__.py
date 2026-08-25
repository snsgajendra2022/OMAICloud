"""API Gateway — routes to enterprise services + policy checks."""
from __future__ import annotations

import time
from typing import Any

from services._common import ServiceHealth, ok
from services.agent_service import AgentService
from services.audit_service import AuditService
from services.billing_service import BillingService
from services.evaluation_service import EvaluationService
from services.identity_service import IdentityService
from services.knowledge_service import KnowledgeService
from services.learning_service import LearningService
from services.memory_service import MemoryService
from services.model_lifecycle import ModelLifecycleService
from services.model_service import ModelGateway
from services.reasoning_service import ReasoningService
from services.retrieval_service import RetrievalService
from services.user_service import UserService


class APIGateway:
    """Single entry for enterprise OM platform (in-process mesh for local/prod)."""

    def __init__(self) -> None:
        self.identity = IdentityService()
        self.users = UserService()
        self.billing = BillingService()
        self.audit = AuditService()
        self.models = ModelGateway()
        self.lifecycle = ModelLifecycleService()
        self.agents = AgentService()
        self.reasoning = ReasoningService()
        self.knowledge = KnowledgeService()
        self.retrieval = RetrievalService()
        self.memory = MemoryService()
        self.evaluation = EvaluationService()
        self.learning = LearningService()

    def health(self) -> dict[str, Any]:
        services = {
            "identity": self.identity.health(),
            "users": self.users.health(),
            "billing": self.billing.health(),
            "audit": self.audit.health(),
            "model_gateway": self.models.health(),
            "model_lifecycle": self.lifecycle.health(),
            "agents": self.agents.health(),
            "reasoning": self.reasoning.health(),
            "knowledge": self.knowledge.health(),
            "retrieval": self.retrieval.health(),
            "memory": self.memory.health(),
            "evaluation": self.evaluation.health(),
            "learning": self.learning.health(),
        }
        unhealthy = [k for k, v in services.items() if v.get("status") != "healthy"]
        return ServiceHealth(
            "api-gateway",
            status="degraded" if unhealthy else "healthy",
            detail={"services": services, "unhealthy": unhealthy},
        ).to_dict()

    def handle(self, route: str, **kwargs: Any) -> dict[str, Any]:
        tenant = str(kwargs.get("tenant_id") or "default")
        actor = str(kwargs.get("actor") or kwargs.get("user_id") or "")
        self.audit.log(route, actor=actor, tenant_id=tenant, meta={"keys": list(kwargs.keys())})

        if route in {"chat", "generate", "model"}:
            out = self.models.route(str(kwargs.get("prompt") or kwargs.get("question") or ""))
            if out.get("ok") and isinstance(out.get("data"), dict):
                usage = out["data"].get("usage") or {}
                self.billing.record_usage(
                    tenant_id=tenant,
                    tokens_in=int(usage.get("tokens_in") or 0),
                    tokens_out=int(usage.get("tokens_out") or 0),
                    model=str(out["data"].get("model") or "om-1.0"),
                )
            return out
        if route == "reason":
            return self.reasoning.analyze(str(kwargs.get("question") or ""))
        if route == "agent":
            return self.agents.run(str(kwargs.get("task") or ""), root=str(kwargs.get("root") or "."))
        if route == "knowledge.search":
            return self.knowledge.search(str(kwargs.get("query") or ""))
        if route == "knowledge.ingest":
            return self.knowledge.ingest(str(kwargs.get("path") or ""))
        if route == "retrieve":
            return self.retrieval.search(str(kwargs.get("query") or ""))
        if route == "memory.recall":
            return self.memory.recall(str(kwargs.get("query") or ""), layer=kwargs.get("layer"))
        if route == "evaluate":
            return self.evaluation.run()
        if route == "improve":
            return self.learning.improve(str(kwargs.get("question") or ""), str(kwargs.get("answer") or ""))
        if route == "identity":
            return self.identity.status()
        if route == "users.create":
            return self.users.create(str(kwargs.get("email") or "user@om.local"), role=str(kwargs.get("role") or "viewer"))
        if route == "users.list":
            return self.users.list_users()
        if route == "billing.summary":
            return self.billing.summary(tenant)
        if route == "audit.recent":
            return self.audit.recent()
        if route == "lifecycle.status":
            return self.lifecycle.status()
        if route == "lifecycle.promote":
            return self.lifecycle.promote(str(kwargs.get("model_id") or "om-1.0"), str(kwargs.get("state") or "candidate"))
        if route == "metrics":
            return ok(
                {
                    "model": self.models.metrics(),
                    "billing": self.billing.summary(tenant).get("data"),
                    "lifecycle": self.lifecycle.status().get("data"),
                }
            )
        if route == "security":
            from security.authentication import status as auth_status

            return ok(auth_status())
        return {"ok": False, "error": f"unknown route: {route}"}
