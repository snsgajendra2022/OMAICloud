"""Scoped permission checks; default deny without explicit grants."""
from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock

from .action_request import ActionRequest, RiskClass
from .permission import Permission, PermissionDecision


class PermissionManager:
    def __init__(self, *, allow_everything_forever: bool = False) -> None:
        self._lock = RLock()
        self._grants: list[Permission] = []
        self._allow_everything_forever = allow_everything_forever

    @property
    def allow_everything_forever(self) -> bool:
        return self._allow_everything_forever

    @allow_everything_forever.setter
    def allow_everything_forever(self, value: bool) -> None:
        self._allow_everything_forever = bool(value)

    def grant(self, permission: Permission) -> None:
        with self._lock:
            self._grants.append(permission)

    def revoke_subject(self, subject: str) -> int:
        with self._lock:
            before = len(self._grants)
            self._grants = [g for g in self._grants if g.subject != subject]
            return before - len(self._grants)

    def check(self, request: ActionRequest) -> PermissionDecision:
        if self._allow_everything_forever:
            return PermissionDecision.ALLOW

        now = datetime.now(timezone.utc)
        with self._lock:
            for grant in self._grants:
                if not grant.is_active(now):
                    continue
                if grant.subject not in {request.actor, "*"}:
                    continue
                if grant.action_type not in {request.action_type, "*"}:
                    continue
                if not _risk_covers(grant.risk_class, request.risk_class):
                    continue
                return grant.decision

        if request.is_auto_eligible():
            return PermissionDecision.ALLOW

        if request.risk_class in {RiskClass.SENSITIVE, RiskClass.DESTRUCTIVE}:
            return PermissionDecision.NEEDS_APPROVAL

        if request.requires_explicit_approval:
            return PermissionDecision.NEEDS_APPROVAL

        return PermissionDecision.DENY


def _risk_covers(granted: RiskClass, required: RiskClass) -> bool:
    order = list(RiskClass)
    return order.index(granted) >= order.index(required)
