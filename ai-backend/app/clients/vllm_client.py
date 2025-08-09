from __future__ import annotations

from typing import Any, Dict

import httpx
from fastapi import HTTPException, status

from ..config import get_settings
from ..deps import route_registry


class UpstreamError(Exception):
    pass


def _map_upstream_error(exc: Exception) -> HTTPException:
    if isinstance(exc, httpx.ConnectTimeout) or isinstance(exc, httpx.ReadTimeout):
        return HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Upstream timeout")
    if isinstance(exc, httpx.ConnectError):
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Cannot connect to upstream")
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        # Map common OpenAI/vLLM statuses
        if status_code in (400, 401, 403, 404, 409, 422):
            return HTTPException(status_code=status_code, detail=exc.response.text)
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Upstream error: {status_code}")
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Upstream error")


async def list_models(route_key: str) -> Dict[str, Any]:
    client = route_registry.get_client(route_key)
    try:
        resp = await client.get("/models")
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # noqa: B902
        raise _map_upstream_error(exc)  # type: ignore[misc]


async def create_chat_completion(route_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    client = route_registry.get_client(route_key)
    try:
        resp = await client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # noqa: B902
        raise _map_upstream_error(exc)  # type: ignore[misc]


async def stream_chat_completion(route_key: str, payload: Dict[str, Any]) -> httpx.Response:
    client = route_registry.get_client(route_key)
    # Build request and send with stream=True so caller can iterate lines
    try:
        request = client.build_request("POST", "/chat/completions", json=payload)
        resp = await client.send(request, stream=True, timeout=httpx.Timeout(None, read=get_settings().read_timeout_seconds))
        resp.raise_for_status()
        return resp
    except Exception as exc:  # noqa: B902
        raise _map_upstream_error(exc)  # type: ignore[misc]


async def create_embedding(route_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    client = route_registry.get_client(route_key)
    try:
        resp = await client.post("/embeddings", json=payload)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # noqa: B902
        raise _map_upstream_error(exc)  # type: ignore[misc]
