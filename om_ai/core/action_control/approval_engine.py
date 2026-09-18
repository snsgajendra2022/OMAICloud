"""Human-in-the-loop approval queue with audit persistence."""
from __future__ import annotations

from threading import RLock

from .action_audit import ActionAudit
from .action_request import ActionRequest


class ApprovalEngine:
    def __init__(self, audit: ActionAudit | None = None) -> None:
        self.audit = audit or ActionAudit()
        self._lock = RLock()
        self._pending: dict[str, ActionRequest] = {}
        self._decisions: dict[str, bool] = {}

    def enqueue(self, request: ActionRequest) -> str:
        with self._lock:
            self._pending[request.action_id] = request
        self.audit.log_approval_pending(request)
        return request.action_id

    def pending(self) -> list[ActionRequest]:
        with self._lock:
            return list(self._pending.values())

    def approve(self, action_id: str, *, approver: str) -> bool:
        with self._lock:
            if action_id not in self._pending:
                return False
            self._decisions[action_id] = True
            del self._pending[action_id]
        self.audit.log_approval_decision(action_id, approved=True, approver=approver)
        return True

    def deny(self, action_id: str, *, approver: str) -> bool:
        with self._lock:
            if action_id not in self._pending:
                return False
            self._decisions[action_id] = False
            del self._pending[action_id]
        self.audit.log_approval_decision(action_id, approved=False, approver=approver)
        return True

    def is_approved(self, action_id: str) -> bool | None:
        with self._lock:
            if action_id in self._pending:
                return None
            if action_id in self._decisions:
                return self._decisions[action_id]
        return None
