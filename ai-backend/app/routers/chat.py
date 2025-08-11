from __future__ import annotations

import asyncio
import contextlib
import json
import time
from typing import Any, AsyncIterator, Dict, Optional
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from ..clients import vllm_client
import gzip
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
    conversation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


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
    # Persist user/assistant messages
    from ..db.base import get_session
    from ..db.models import Conversation, Message
    db = get_session()
    try:
        conv_id = payload.conversation_id
        if not conv_id:
            conv = Conversation(metadata_json=payload.metadata or None)
            db.add(conv)
            db.flush()
            conv_id = conv.id

        user_msg = Message(
            conversation_id=conv_id,
            role="user",
            content_text=payload.message,
            system_prompt=payload.system,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            model=model,
            model_key=route_key,
            status="completed",
        )
        # Store raw request gzip
        try:
            user_msg.raw_request_gzip = gzip.compress(json.dumps(body).encode("utf-8"))
        except Exception:
            pass
        db.add(user_msg)
        db.flush()

        # Store raw request gzip
        try:
            user_msg.raw_request_gzip = gzip.compress(json.dumps(body).encode("utf-8"))
        except Exception:
            pass

        resp = await vllm_client.create_chat_completion(route_key, body)

        usage = resp.get("usage") or {}
        content = None
        choices = resp.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            content = msg.get("content")

        asst = Message(
            conversation_id=conv_id,
            role="assistant",
            content_text=content,
            model=model,
            model_key=route_key,
            status="completed",
            upstream_id=resp.get("id"),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
        )
        db.add(asst)
        try:
            asst.raw_response_gzip = gzip.compress(json.dumps(resp).encode("utf-8"))
        except Exception:
            pass
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return resp


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

    # Set up persistence for streaming
    from ..db.base import get_session
    from ..db.models import Conversation, Message, MessageStream
    db = get_session()
    conv_id = payload.conversation_id
    try:
        if not conv_id:
            conv = Conversation(metadata_json=payload.metadata or None)
            db.add(conv)
            db.flush()
            conv_id = conv.id

        user_msg = Message(
            conversation_id=conv_id,
            role="user",
            content_text=payload.message,
            system_prompt=payload.system,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            model=model,
            model_key=route_key,
            status="completed",
        )
        # Store raw request gzip
        try:
            user_msg.raw_request_gzip = gzip.compress(json.dumps(body).encode("utf-8"))
        except Exception:
            pass
        db.add(user_msg)
        db.flush()

        asst_msg = Message(
            conversation_id=conv_id,
            role="assistant",
            content_text="",
            model=model,
            model_key=route_key,
            status="in_progress",
        )
        db.add(asst_msg)
        db.flush()
        db.commit()
    except Exception:
        db.rollback()
        db.close()
        raise

    async def generator() -> AsyncIterator[bytes]:
        raw_sse_lines: list[str] = []
        assembled: list[str] = []

        async for chunk in _stream_upstream_and_heartbeat(
            request,
            upstream_resp,
            heartbeat_interval=15.0,
            total_timeout=settings.total_timeout_seconds,
        ):
            try:
                s = chunk.decode("utf-8", errors="ignore")
            except Exception:
                s = ""
            if s.startswith("data:"):
                raw_sse_lines.append(s)
                try:
                    payload_json = json.loads(s[len("data:"):].strip())
                    ch = (payload_json.get("choices") or [{}])[0]
                    delta = ch.get("delta") or {}
                    if "content" in delta and delta["content"]:
                        assembled.append(delta["content"])
                except Exception:
                    pass
            yield chunk

        # Persist raw SSE and finalize assistant message
        final_text = "".join(assembled)
        raw_joined = "".join(raw_sse_lines)
        db2 = get_session()
        try:
            # Compress raw SSE for storage efficiency
            try:
                raw_gz = gzip.compress(raw_joined.encode("utf-8"))
            except Exception:
                raw_gz = None
            if raw_gz is not None:
                db2.add(MessageStream(message_id=asst_msg.id, raw_sse_gzip=raw_gz))
            m = db2.query(Message).get(asst_msg.id)  # type: ignore
            if m:
                m.content_text = final_text
                m.status = "completed"
                m.completed_at = datetime.utcnow()
            db2.commit()
        except Exception:
            db2.rollback()
        finally:
            db2.close()

    return StreamingResponse(generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})
