"""STEP 33 — OM Enterprise Memory."""
from om_ai.core.enterprise_memory import EnterpriseMemory, run_enterprise_memory

__all__ = ["EnterpriseMemory", "run_enterprise_memory", "Step33EnterpriseMemory"]


class Step33EnterpriseMemory(EnterpriseMemory):
    step = 33
