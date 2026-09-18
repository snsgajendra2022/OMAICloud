"""STEP 27 — Response Intelligence Upgrade."""
from om_ai.core.response.response_intelligence import ResponseIntelligence, run_response_intelligence

__all__ = ["ResponseIntelligence", "run_response_intelligence", "Step27ResponseIntelligence"]


class Step27ResponseIntelligence(ResponseIntelligence):
    step = 27
