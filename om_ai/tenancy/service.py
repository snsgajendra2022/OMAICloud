"""OM AI Tenancy Service — SQLite-backed persistent tenant directory."""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

logger = logging.getLogger(__name__)

_DEFAULT_DB = "artifacts/om_ai.sqlite3"

_DDL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS organizations (
    org_id      TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    metadata    TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id   TEXT PRIMARY KEY,
    org_id      TEXT NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    metadata    TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_tenant_org ON tenants(org_id);

CREATE TABLE IF NOT EXISTS ai_employees (
    employee_id         TEXT NOT NULL,
    tenant_id           TEXT NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    role                TEXT NOT NULL,
    objective           TEXT NOT NULL DEFAULT '',
    system_instructions TEXT NOT NULL DEFAULT '',
    approved_tools      TEXT NOT NULL DEFAULT '[]',
    memory_namespace    TEXT NOT NULL DEFAULT 'default',
    knowledge_namespace TEXT NOT NULL DEFAULT 'default',
    escalation_rules    TEXT NOT NULL DEFAULT '{}',
    enabled             INTEGER NOT NULL DEFAULT 1,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    PRIMARY KEY (employee_id, tenant_id)
);
CREATE INDEX IF NOT EXISTS idx_employee_tenant ON ai_employees(tenant_id);
"""


@dataclass
class Organization:
    org_id: str
    name: str
    created_at: str
    metadata: dict = field(default_factory=dict)


@dataclass
class Tenant:
    tenant_id: str
    org_id: str
    name: str
    created_at: str
    metadata: dict = field(default_factory=dict)


@dataclass
class AIEmployee:
    employee_id: str
    tenant_id: str
    name: str
    role: str
    objective: str = ""
    system_instructions: str = ""
    approved_tools: list[str] = field(default_factory=list)
    memory_namespace: str = "default"
    knowledge_namespace: str = "default"
    escalation_rules: dict = field(default_factory=dict)
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TenantDirectory:
    """Persistent, thread-safe directory for organizations, tenants, and AI employees.

    All data is stored in a SQLite database.  The directory supports strict tenant
    isolation: operations that cross tenant boundaries raise ``PermissionError``.
    """

    def __init__(self, db_path: str | Path = _DEFAULT_DB) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        if not getattr(self._local, "conn", None):
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        yield self._local.conn

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(_DDL)
            conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------ #
    #  Organizations                                                        #
    # ------------------------------------------------------------------ #

    def create_organization(self, name: str, metadata: dict | None = None) -> Organization:
        org = Organization(
            org_id=uuid.uuid4().hex,
            name=name,
            created_at=self._now(),
            metadata=metadata or {},
        )
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO organizations (org_id, name, created_at, metadata) VALUES (?,?,?,?)",
                (org.org_id, org.name, org.created_at, json.dumps(org.metadata)),
            )
            conn.commit()
        return org

    def get_organization(self, org_id: str) -> Organization | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM organizations WHERE org_id = ?", (org_id,)
            ).fetchone()
        if not row:
            return None
        return Organization(
            org_id=row["org_id"],
            name=row["name"],
            created_at=row["created_at"],
            metadata=json.loads(row["metadata"]),
        )

    # ------------------------------------------------------------------ #
    #  Tenants                                                              #
    # ------------------------------------------------------------------ #

    def create_tenant(self, org_id: str, name: str, metadata: dict | None = None) -> Tenant:
        tenant = Tenant(
            tenant_id=uuid.uuid4().hex,
            org_id=org_id,
            name=name,
            created_at=self._now(),
            metadata=metadata or {},
        )
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO tenants (tenant_id, org_id, name, created_at, metadata) VALUES (?,?,?,?,?)",
                (tenant.tenant_id, tenant.org_id, tenant.name, tenant.created_at, json.dumps(tenant.metadata)),
            )
            conn.commit()
        return tenant

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM tenants WHERE tenant_id = ?", (tenant_id,)
            ).fetchone()
        if not row:
            return None
        return Tenant(
            tenant_id=row["tenant_id"],
            org_id=row["org_id"],
            name=row["name"],
            created_at=row["created_at"],
            metadata=json.loads(row["metadata"]),
        )

    def list_tenants(self, org_id: str) -> list[Tenant]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM tenants WHERE org_id = ? ORDER BY created_at", (org_id,)
            ).fetchall()
        return [
            Tenant(
                tenant_id=r["tenant_id"],
                org_id=r["org_id"],
                name=r["name"],
                created_at=r["created_at"],
                metadata=json.loads(r["metadata"]),
            )
            for r in rows
        ]

    # ------------------------------------------------------------------ #
    #  AI Employees                                                         #
    # ------------------------------------------------------------------ #

    def upsert(self, emp: AIEmployee) -> AIEmployee:
        """Insert or replace an AI employee record."""
        emp.updated_at = self._now()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO ai_employees
                    (employee_id, tenant_id, name, role, objective, system_instructions,
                     approved_tools, memory_namespace, knowledge_namespace,
                     escalation_rules, enabled, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(employee_id, tenant_id) DO UPDATE SET
                    name=excluded.name,
                    role=excluded.role,
                    objective=excluded.objective,
                    system_instructions=excluded.system_instructions,
                    approved_tools=excluded.approved_tools,
                    memory_namespace=excluded.memory_namespace,
                    knowledge_namespace=excluded.knowledge_namespace,
                    escalation_rules=excluded.escalation_rules,
                    enabled=excluded.enabled,
                    updated_at=excluded.updated_at
                """,
                (
                    emp.employee_id,
                    emp.tenant_id,
                    emp.name,
                    emp.role,
                    emp.objective,
                    emp.system_instructions,
                    json.dumps(emp.approved_tools),
                    emp.memory_namespace,
                    emp.knowledge_namespace,
                    json.dumps(emp.escalation_rules),
                    1 if emp.enabled else 0,
                    emp.created_at,
                    emp.updated_at,
                ),
            )
            conn.commit()
        return emp

    def get_employee(self, tenant_id: str, employee_id: str) -> AIEmployee | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM ai_employees WHERE tenant_id = ? AND employee_id = ?",
                (tenant_id, employee_id),
            ).fetchone()
        if not row:
            return None
        return self._row_to_employee(row)

    def list_employees(self, tenant_id: str, enabled_only: bool = False) -> list[AIEmployee]:
        sql = "SELECT * FROM ai_employees WHERE tenant_id = ?"
        params: list[Any] = [tenant_id]
        if enabled_only:
            sql += " AND enabled = 1"
        sql += " ORDER BY created_at"
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_employee(r) for r in rows]

    def delete_employee(self, tenant_id: str, employee_id: str) -> bool:
        with self._conn() as conn:
            cur = conn.execute(
                "DELETE FROM ai_employees WHERE tenant_id = ? AND employee_id = ?",
                (tenant_id, employee_id),
            )
            conn.commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------ #
    #  Tenant isolation                                                     #
    # ------------------------------------------------------------------ #

    def assert_tenant_owns(self, caller_tenant_id: str, resource_tenant_id: str) -> None:
        """Raise PermissionError if caller does not own the resource tenant."""
        if caller_tenant_id != resource_tenant_id:
            raise PermissionError(
                f"Tenant '{caller_tenant_id}' is not allowed to access "
                f"resources of tenant '{resource_tenant_id}'."
            )

    def assert_employee_in_tenant(self, tenant_id: str, employee_id: str) -> AIEmployee:
        """Return the employee or raise ValueError if not found in this tenant."""
        emp = self.get_employee(tenant_id, employee_id)
        if emp is None:
            raise ValueError(f"Employee '{employee_id}' not found in tenant '{tenant_id}'.")
        return emp

    # ------------------------------------------------------------------ #
    #  Legacy / compatibility shim                                          #
    # ------------------------------------------------------------------ #

    def get(self, tenant_id: str, employee_id: str) -> AIEmployee | None:
        """Alias for get_employee (backward compatibility)."""
        return self.get_employee(tenant_id, employee_id)

    def list(self, tenant_id: str) -> list[AIEmployee]:
        """Alias for list_employees (backward compatibility)."""
        return self.list_employees(tenant_id)

    # ------------------------------------------------------------------ #
    #  Internal                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _row_to_employee(row: sqlite3.Row) -> AIEmployee:
        return AIEmployee(
            employee_id=row["employee_id"],
            tenant_id=row["tenant_id"],
            name=row["name"],
            role=row["role"],
            objective=row["objective"],
            system_instructions=row["system_instructions"],
            approved_tools=json.loads(row["approved_tools"]),
            memory_namespace=row["memory_namespace"],
            knowledge_namespace=row["knowledge_namespace"],
            escalation_rules=json.loads(row["escalation_rules"]),
            enabled=bool(row["enabled"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
