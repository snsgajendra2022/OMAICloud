"""STEP 35 — OM Production Platform."""
from om_ai.core.production_platform import ProductionPlatform, run_production_platform

__all__ = ["ProductionPlatform", "run_production_platform", "Step35ProductionPlatform"]


class Step35ProductionPlatform(ProductionPlatform):
    step = 35
