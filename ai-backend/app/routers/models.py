from __future__ import annotations

from typing import List

from fastapi import APIRouter

from ..config import get_settings
from ..deps import route_registry

router = APIRouter(prefix="/models")


@router.get("")
async def list_models() -> dict:
    settings = get_settings()
    aggregated = await route_registry.aggregate_models()
    if settings.allowed_models_list:
        allowed = set(settings.allowed_models_list)
        aggregated = [m for m in aggregated if m.get("id") in allowed]
    # Return OpenAI-compatible envelope
    return {"object": "list", "data": aggregated}
