from __future__ import annotations

import gzip
from typing import Optional

from fastapi import APIRouter, HTTPException

from ..db.base import get_session
from ..db.models import Message, MessageStream


router = APIRouter(prefix="/messages")


@router.get("/{message_id}/raw")
def get_message_raw(message_id: str) -> dict:
    db = get_session()
    try:
        msg = db.get(Message, message_id)
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")

        def _decompress(b: Optional[bytes]) -> Optional[str]:
            if not b:
                return None
            try:
                return gzip.decompress(b).decode("utf-8", errors="replace")
            except Exception:
                return None

        raw_req = _decompress(msg.raw_request_gzip)
        raw_resp = _decompress(msg.raw_response_gzip)
        stream_row = db.query(MessageStream).filter(MessageStream.message_id == message_id).order_by(MessageStream.created_at.desc()).first()
        raw_sse = _decompress(stream_row.raw_sse_gzip) if stream_row else None

        return {
            "message_id": message_id,
            "raw_request_json": raw_req,
            "raw_response_json": raw_resp,
            "raw_sse": raw_sse,
        }
    finally:
        db.close()


