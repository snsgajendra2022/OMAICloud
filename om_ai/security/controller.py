"""
OM Autonomous Security Controller

Combines:

- Policy validation
- Permission checking
- Sandbox execution
- Audit logging
"""
from __future__ import annotations

from .audit import AuditLog
from .audit_log import AuditLogger
from .policy import SecurityPolicy
from .permission import PermissionManager
from .sandbox import SandboxRunner





class SecurityController:



    def __init__(self):
        self.policy = SecurityPolicy()
        self.permission = PermissionManager()
        self.sandbox = SandboxRunner()
        self.audit_log = AuditLogger()
        self.audit = AuditLog()

    def _record(
        self,
        *,
        tenant_id: str,
        actor: str,
        action: str,
        resource: str,
        detail: dict | None = None,
    ) -> None:
        payload = {
            "tenant_id": tenant_id,
            "actor": actor,
            "action": action,
            "resource": resource,
            "detail": detail or {},
        }
        self.audit.record(
            tenant_id=tenant_id,
            actor=actor,
            action=action,
            resource=resource,
            detail=detail,
        )
        self.audit_log.log(payload)

    def execute(

        self,

        agent: str,

        action: str,

        function,

        *,

        tenant_id="default",

        resource="tool_execution",

        permission=None,

        **kwargs

    ):


        # -------------------------
        # Permission Check
        # -------------------------

        if permission:


            allowed = self.permission.check(

                agent,

                permission

            )


            if not allowed:


                self._record(

                    tenant_id=tenant_id,

                    actor=agent,

                    action="permission.denied",

                    resource=resource,

                    detail={

                        "action":action

                    }

                )


                return {


                    "success":False,

                    "reason":

                    "permission denied"

                }



        # -------------------------
        # Security Policy
        # -------------------------

        policy_result = self.policy.check(

            action

        )


        if not policy_result["allowed"]:



            self._record(

                tenant_id=tenant_id,

                actor=agent,

                action="security.blocked",

                resource=resource,

                detail={

                    "action":action,

                    "reason":

                    policy_result["reason"]

                }

            )


            return {


                "success":False,

                "reason":

                policy_result["reason"]

            }





        # -------------------------
        # Sandbox Execute
        # -------------------------

        result = self.sandbox.execute(

            function,

            **kwargs

        )





        # -------------------------
        # Audit Success / Failure
        # -------------------------

        self._record(

            tenant_id=tenant_id,

            actor=agent,

            action="tool.execute",

            resource=resource,

            detail={

                "action":action,

                "result":result

            }

        )



        return result