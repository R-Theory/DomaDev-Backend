from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from sqlalchemy import text
from ..db.base import get_session
from ..db.models import Message


router = APIRouter(prefix="/search")


class SearchMessageOut(BaseModel):
    id: str
    conversation_id: str
    role: str
    content_text: Optional[str] = None
    model: Optional[str] = None
    started_at: Any

    class Config:
        from_attributes = True


@router.get("/messages")
def search_messages(
    q: str = Query(..., min_length=1),
    conversation_id: Optional[str] = None,
    role: Optional[str] = None,
    model: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> List[SearchMessageOut]:
    # Use raw SQL against FTS5 table, then join to messages
    db = get_session()
    try:
        # Base FTS query
        base_sql = "SELECT message_id FROM messages_fts WHERE messages_fts MATCH :q"
        params: dict[str, Any] = {"q": q}

        # Fetch candidate message ids ordered by bm25 ranking
        sql = base_sql + " ORDER BY bm25(messages_fts) LIMIT :limit OFFSET :offset"
        params.update({"limit": limit, "offset": offset})
        rows = db.execute(text(sql), params).fetchall()
        ids = [r[0] for r in rows]
        if not ids:
            return []

        # Load messages and apply optional filters
        mq = db.query(Message).filter(Message.id.in_(ids))
        if conversation_id:
            mq = mq.filter(Message.conversation_id == conversation_id)
        if role:
            mq = mq.filter(Message.role == role)
        if model:
            mq = mq.filter(Message.model == model)
        # Preserve FTS order roughly by started_at desc if needed
        msgs = mq.order_by(Message.started_at.desc()).all()
        return [SearchMessageOut.model_validate(m) for m in msgs]
    finally:
        db.close()


