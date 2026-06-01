"""Automation API endpoints for external clients."""

from fastapi import APIRouter, Depends

from ..auth import require_automation_auth
from ..services.automation import (
    get_automation_status,
    start_automation_processing,
    stop_automation_processing,
)

router = APIRouter(
    prefix="/api/automation",
    tags=["automation"],
    dependencies=[Depends(require_automation_auth)],
)


@router.get("/status")
async def status():
    """Return the current processing state."""
    return get_automation_status()


@router.post("/process/start")
async def start_process_all():
    """Start processing all tagged documents in the background."""
    return await start_automation_processing()


@router.post("/process/stop")
async def stop_process_all():
    """Stop an automation-owned processing run."""
    return await stop_automation_processing()
