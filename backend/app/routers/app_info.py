"""Application metadata endpoint."""

import os

from fastapi import APIRouter

router = APIRouter(prefix="/api/app-info", tags=["app-info"])


@router.get("")
async def get_app_info():
    return {
        "version": os.environ.get("APP_VERSION", "dev"),
    }
