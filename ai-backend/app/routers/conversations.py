from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..db.base import get_session
from ..db.models import Conversation, Message


router = APIRouter(prefix="/conversations")


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    pinned: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None


class ConversationOut(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: Any
    pinned: bool = False
    metadata_json: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: str
    role: str
    content_text: Optional[str] = None
    model: Optional[str] = None
    model_key: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    started_at: Any
    completed_at: Optional[Any] = None

    class Config:
        from_attributes = True


@router.post("")
def create_conversation(payload: ConversationCreate) -> ConversationOut:
    db = get_session()
    try:
        conv = Conversation(title=payload.title, metadata_json=payload.metadata or None)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return ConversationOut.model_validate(conv)
    finally:
        db.close()


@router.get("")
def list_conversations(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)) -> List[ConversationOut]:
    db = get_session()
    try:
        rows = (
            db.query(Conversation)
            .order_by(Conversation.pinned.desc(), Conversation.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [ConversationOut.model_validate(r) for r in rows]
    finally:
        db.close()


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str) -> ConversationOut:
    db = get_session()
    try:
        conv = db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return ConversationOut.model_validate(conv)
    finally:
        db.close()


@router.patch("/{conversation_id}")
def update_conversation(conversation_id: str, payload: ConversationUpdate) -> ConversationOut:
    db = get_session()
    try:
        conv = db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if payload.title is not None:
            conv.title = payload.title
        if payload.pinned is not None:
            conv.pinned = payload.pinned
        if payload.metadata is not None:
            conv.metadata_json = payload.metadata
        
        db.commit()
        db.refresh(conv)
        return ConversationOut.model_validate(conv)
    finally:
        db.close()


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str) -> dict:
    db = get_session()
    try:
        conv = db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        db.delete(conv)
        db.commit()
        return {"deleted": True}
    finally:
        db.close()


@router.get("/{conversation_id}/messages")
def list_conversation_messages(
    conversation_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order: str = Query("asc", pattern="^(asc|desc)$"),
) -> List[MessageOut]:
    db = get_session()
    try:
        if not db.get(Conversation, conversation_id):
            raise HTTPException(status_code=404, detail="Conversation not found")
        q = db.query(Message).filter(Message.conversation_id == conversation_id)
        q = q.order_by(Message.started_at.asc() if order == "asc" else Message.started_at.desc())
        rows = q.offset(offset).limit(limit).all()
        return [MessageOut.model_validate(r) for r in rows]
    finally:
        db.close()


