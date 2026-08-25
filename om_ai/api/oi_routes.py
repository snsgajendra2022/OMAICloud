"""Operating Intelligence API — capability board + Observe→Improve cycle."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from om_ai.api.deps import require_auth
from om_ai.operating_intelligence import capability_status, run_cycle
from om_ai.operating_intelligence.embodiment import electronics, sensors

router = APIRouter(prefix="/v1/oi", tags=["Operating Intelligence"])


class CycleRequest(BaseModel):
    goal: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = True


class HardwareCommand(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = True


class SensorIngest(BaseModel):
    reading: dict[str, Any] = Field(default_factory=dict)


@router.get("/status")
def oi_status(_auth=Depends(require_auth)):
    return capability_status()


@router.post("/cycle")
def oi_cycle(body: CycleRequest, _auth=Depends(require_auth)):
    result = run_cycle(body.goal, context=body.context, dry_run=body.dry_run)
    return result.to_dict()


@router.post("/hardware/command")
def oi_hardware(body: HardwareCommand, _auth=Depends(require_auth)):
    # Always dry-run unless explicitly false AND future allow-list passes.
    return electronics.command(body.payload, dry_run=body.dry_run if body.dry_run else True)


@router.post("/sensors/ingest")
def oi_sensors(body: SensorIngest, _auth=Depends(require_auth)):
    return sensors.ingest(body.reading)
