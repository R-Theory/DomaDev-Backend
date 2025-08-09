from __future__ import annotations

from fastapi import APIRouter

from ..config import get_settings
from ..deps import route_registry

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    vllm_status = "unknown"
    # Try default route if configured
    try:
        default_key = settings.default_model_key or (route_registry.list_route_keys()[0] if route_registry.list_route_keys() else "")
        if default_key:
            client = route_registry.get_client(default_key)
            resp = await client.get("/models")
            vllm_status = "ok" if resp.is_success else "unavailable"
        else:
            vllm_status = "unconfigured"
    except Exception:
        vllm_status = "unavailable"
    return {"ok": True, "vllm": vllm_status}
