from __future__ import annotations

import json
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from datetime import datetime

from ..db.base import get_session
from ..db.models import Conversation, Message, MessageStream


router = APIRouter(prefix="/backup")


@router.get("/export")
def export_all() -> Dict[str, Any]:
    db = get_session()
    try:
        convs = db.query(Conversation).all()
        msgs = db.query(Message).all()
        streams = db.query(MessageStream).all()

        def to_dict_conv(c: Conversation) -> Dict[str, Any]:
            return {
                "id": c.id,
                "title": c.title,
                "created_at": c.created_at.isoformat(),
                "metadata_json": c.metadata_json,
            }

        def to_dict_msg(m: Message) -> Dict[str, Any]:
            return {
                "id": m.id,
                "conversation_id": m.conversation_id,
                "parent_id": m.parent_id,
                "role": m.role,
                "content_text": m.content_text,
                "content_json": m.content_json,
                "model": m.model,
                "model_key": m.model_key,
                "system_prompt": m.system_prompt,
                "temperature": m.temperature,
                "max_tokens": m.max_tokens,
                "upstream_id": m.upstream_id,
                # Raw blobs omitted in JSON export to keep size down
                "prompt_tokens": m.prompt_tokens,
                "completion_tokens": m.completion_tokens,
                "total_tokens": m.total_tokens,
                "status": m.status,
                "error_text": m.error_text,
                "started_at": m.started_at.isoformat(),
                "completed_at": m.completed_at.isoformat() if m.completed_at else None,
            }

        def to_dict_stream(s: MessageStream) -> Dict[str, Any]:
            return {
                "id": s.id,
                "message_id": s.message_id,
                "created_at": s.created_at.isoformat(),
                # raw_sse_gzip omitted
            }

        return {
            "conversations": [to_dict_conv(c) for c in convs],
            "messages": [to_dict_msg(m) for m in msgs],
            "streams": [to_dict_stream(s) for s in streams],
        }
    finally:
        db.close()


@router.post("/import")
def import_all(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = get_session()
    imported = {"conversations": 0, "messages": 0, "streams": 0}
    try:
        # Conversations
        for c in payload.get("conversations", []):
            if not c.get("id"):
                continue
            exist = db.get(Conversation, c["id"])  # type: ignore[arg-type]
            if exist:
                continue
            conv = Conversation(
                id=c["id"],
                title=c.get("title"),
                created_at=datetime.fromisoformat(c["created_at"]) if c.get("created_at") else datetime.utcnow(),
                metadata_json=c.get("metadata_json"),
            )
            db.add(conv)
            imported["conversations"] += 1

        db.flush()

        # Messages
        for m in payload.get("messages", []):
            if not m.get("id") or not m.get("conversation_id"):
                continue
            exist = db.get(Message, m["id"])  # type: ignore[arg-type]
            if exist:
                continue
            msg = Message(
                id=m["id"],
                conversation_id=m["conversation_id"],
                parent_id=m.get("parent_id"),
                role=m.get("role", "user"),
                content_text=m.get("content_text"),
                content_json=m.get("content_json"),
                model=m.get("model"),
                model_key=m.get("model_key"),
                system_prompt=m.get("system_prompt"),
                temperature=m.get("temperature"),
                max_tokens=m.get("max_tokens"),
                upstream_id=m.get("upstream_id"),
                prompt_tokens=m.get("prompt_tokens"),
                completion_tokens=m.get("completion_tokens"),
                total_tokens=m.get("total_tokens"),
                status=m.get("status", "completed"),
                error_text=m.get("error_text"),
                started_at=datetime.fromisoformat(m["started_at"]) if m.get("started_at") else datetime.utcnow(),
                completed_at=(datetime.fromisoformat(m["completed_at"]) if m.get("completed_at") else None),
            )
            db.add(msg)
            imported["messages"] += 1

        db.flush()

        # Streams (raw gz not included in export)
        for s in payload.get("streams", []):
            if not s.get("id") or not s.get("message_id"):
                continue
            exist = db.query(MessageStream).filter(MessageStream.id == s["id"]).first()
            if exist:
                continue
            stream = MessageStream(
                id=s["id"],
                message_id=s["message_id"],
                created_at=datetime.fromisoformat(s["created_at"]) if s.get("created_at") else datetime.utcnow(),
                raw_sse_gzip=b"",  # placeholder since export omits raw
            )
            db.add(stream)
            imported["streams"] += 1

        db.commit()
        return {"imported": imported}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


