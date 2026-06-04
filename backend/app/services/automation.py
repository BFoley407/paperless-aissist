"""External automation process control.

Provides background start/stop/status helpers for API clients that trigger the
same "process all" workflow as the UI without blocking the HTTP request.
"""

import asyncio
import logging
from typing import Optional

from .scheduler import (
    _clear_processing,
    get_processing_state,
    process_modular_tagged_documents,
    process_tagged_documents,
    try_trigger_processing,
)

logger = logging.getLogger(__name__)

_automation_task: Optional[asyncio.Task] = None
_last_result: Optional[dict] = None


def _is_automation_task_running() -> bool:
    return _automation_task is not None and not _automation_task.done()


async def _run_process_all() -> None:
    global _last_result

    try:
        logger.info("Automation API process-all run started")
        legacy = await process_tagged_documents()
        modular = await process_modular_tagged_documents()
        failed = legacy.get("failed", 0) + modular.get("failed", 0)
        _last_result = {
            "success": failed == 0,
            "status": "completed",
            "processed": legacy.get("processed", 0) + modular.get("processed", 0),
            "failed": failed,
            "results": legacy.get("results", []) + modular.get("results", []),
        }
        logger.info(
            "Automation API process-all run completed: processed=%s failed=%s",
            _last_result["processed"],
            _last_result["failed"],
        )
    except asyncio.CancelledError:
        logger.info("Automation API process-all run cancelled")
        _last_result = {
            "success": False,
            "status": "cancelled",
            "error": "Processing cancelled",
        }
    except Exception as exc:
        logger.error("Automation API process-all run failed: %s", exc)
        _last_result = {
            "success": False,
            "status": "failed",
            "error": str(exc),
        }
    finally:
        _clear_processing()


async def start_automation_processing() -> dict:
    """Start process-all in the background, or report the existing run."""
    global _automation_task

    if _is_automation_task_running():
        return {
            "success": True,
            "status": "already_running",
            "message": "Automation processing already running",
        }

    success, message = try_trigger_processing()
    if not success:
        return {"success": True, "status": "already_running", "message": message}

    _automation_task = asyncio.create_task(_run_process_all())
    return {"success": True, "status": "started", "message": "Processing started"}


async def stop_automation_processing() -> dict:
    """Request cancellation of the current automation-owned run."""
    if not _is_automation_task_running():
        return {
            "success": True,
            "status": "not_running",
            "message": "No automation processing run is active",
        }

    assert _automation_task is not None
    _automation_task.cancel()
    return {
        "success": True,
        "status": "stopping",
        "message": "Automation processing stop requested",
    }


def get_automation_status() -> dict:
    """Return current process state and the last automation result."""
    processing_state = get_processing_state()
    return {
        "success": True,
        "is_processing": processing_state["is_processing"],
        "current_document_ids": processing_state["current_document_ids"],
        "active_documents": processing_state["active_documents"],
        "started_at": processing_state["started_at"],
        "running_seconds": processing_state["running_seconds"],
        "automation_running": _is_automation_task_running(),
        "last_result": _last_result,
    }
