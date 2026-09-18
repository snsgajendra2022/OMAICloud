"""Risk scoring and escalation."""
from __future__ import annotations

from dataclasses import dataclass

from .action_request import ActionRequest, RiskClass


@dataclass(frozen=True)
class RiskAssessment:
    risk_class: RiskClass
    score: float
    reasons: tuple[str, ...]


class RiskEngine:
    _BASE_SCORE: dict[RiskClass, float] = {
        RiskClass.READ_ONLY: 0.1,
        RiskClass.LOW_IMPACT: 0.25,
        RiskClass.REVERSIBLE_WRITE: 0.45,
        RiskClass.EXTERNAL_SIDE_EFFECT: 0.65,
        RiskClass.SENSITIVE: 0.85,
        RiskClass.DESTRUCTIVE: 1.0,
    }

    def assess(self, request: ActionRequest) -> RiskAssessment:
        reasons: list[str] = []
        score = self._BASE_SCORE.get(request.risk_class, 0.5)
        reasons.append(f"declared_risk={request.risk_class.value}")

        if request.source == "external":
            score = min(1.0, score + 0.15)
            reasons.append("external_source_boost")

        if request.action_type.endswith(".delete") or "delete" in request.action_type:
            if request.risk_class != RiskClass.DESTRUCTIVE:
                reasons.append("delete_action_should_be_destructive")

        effective = request.risk_class
        if score >= 0.95:
            effective = RiskClass.DESTRUCTIVE
        elif score >= 0.8:
            effective = RiskClass.SENSITIVE

        return RiskAssessment(
            risk_class=effective,
            score=round(score, 3),
            reasons=tuple(reasons),
        )

    def requires_human_approval(self, assessment: RiskAssessment) -> bool:
        return assessment.risk_class in {
            RiskClass.SENSITIVE,
            RiskClass.DESTRUCTIVE,
            RiskClass.EXTERNAL_SIDE_EFFECT,
        }
