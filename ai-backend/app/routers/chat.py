from __future__ import annotations

import asyncio
import contextlib
import json
import time
from typing import Any, AsyncIterator, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from ..clients import vllm_client
from ..config import get_settings
from ..routing.router import resolve_chat_route_and_model
from ..utils.sse import format_sse_data, heartbeat_sender


class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None
    modelKey: Optional[str] = Field(default=None, description="Routing key to select vLLM instance")
    system: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=1)


router = APIRouter(prefix="/chat")


async def _resolve_route_and_model(payload: ChatRequest) -> tuple[str, str]:
    return await resolve_chat_route_and_model(payload.model, payload.modelKey)


def _build_openai_chat_body(payload: ChatRequest, model: str, stream: bool = False) -> Dict[str, Any]:
    messages = []
    if payload.system:
        messages.append({"role": "system", "content": payload.system})
    messages.append({"role": "user", "content": payload.message})
    body: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }
    if payload.temperature is not None:
        body["temperature"] = payload.temperature
    if payload.max_tokens is not None:
        body["max_tokens"] = payload.max_tokens
    return body


@router.post("")
async def chat(payload: ChatRequest):
    route_key, model = await _resolve_route_and_model(payload)
    body = _build_openai_chat_body(payload, model, stream=False)
    return await vllm_client.create_chat_completion(route_key, body)


async def _stream_upstream_and_heartbeat(
    request: Request,
    upstream_resp: httpx.Response,
    heartbeat_interval: float,
    total_timeout: float,
) -> AsyncIterator[bytes]:
    start_time = time.monotonic()

    async def client_disconnected() -> bool:
        try:
            return await request.is_disconnected()
        except Exception:
            return False

    async def upstream_lines() -> AsyncIterator[bytes]:
        async for line in upstream_resp.aiter_lines():
            if line:
                yield (line + "\n").encode("utf-8")

    heartbeat_it = heartbeat_sender(heartbeat_interval)
    upstream_it = upstream_lines()

    try:
        while True:
            if (time.monotonic() - start_time) > total_timeout:
                yield format_sse_data(json.dumps({"error": {"message": "Upstream timeout"}}), event="error")
                break
            if await client_disconnected():
                # Close upstream response and exit
                await upstream_resp.aclose()
                break
            try:
                upstream_chunk = await asyncio.wait_for(upstream_it.__anext__(), timeout=0.1)
                yield upstream_chunk
                continue
            except StopAsyncIteration:
                break
            except asyncio.TimeoutError:
                pass
            # Heartbeat
            try:
                hb = await asyncio.wait_for(heartbeat_it.__anext__(), timeout=0)
                if hb:
                    yield hb
            except StopAsyncIteration:
                pass
            except asyncio.TimeoutError:
                pass
    finally:
        with contextlib.suppress(Exception):
            await upstream_resp.aclose()


@router.post("/stream")
async def chat_stream(request: Request, payload: ChatRequest):
    settings = get_settings()
    route_key, model = await _resolve_route_and_model(payload)
    body = _build_openai_chat_body(payload, model, stream=True)

    try:
        upstream_resp = await vllm_client.stream_chat_completion(route_key, body)
    except HTTPException as e:
        # Convert error to SSE error response
        data = json.dumps({"error": {"message": e.detail}})
        return StreamingResponse(iter([format_sse_data(data, event="error")]), media_type="text/event-stream")

    return StreamingResponse(
        _stream_upstream_and_heartbeat(
            request,
            upstream_resp,
            heartbeat_interval=15.0,
            total_timeout=settings.total_timeout_seconds,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
