from __future__ import annotations

from typing import Optional, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..db.base import get_session
from ..db.models import Message, Conversation


router = APIRouter(prefix="/conversations/{conversation_id}/messages")


class MessageUpdate(BaseModel):
    content_text: Optional[str] = None
    role: Optional[str] = None


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


class MessageCreate(BaseModel):
    role: str
    content_text: str
    model: Optional[str] = None
    model_key: Optional[str] = None


@router.delete("/{message_id}")
def delete_message(conversation_id: str, message_id: str) -> dict:
    db = get_session()
    try:
        # Verify conversation exists
        conv = db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get and delete message
        msg = db.get(Message, message_id)
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Verify message belongs to conversation
        if msg.conversation_id != conversation_id:
            raise HTTPException(status_code=404, detail="Message not found in conversation")
        
        db.delete(msg)
        db.commit()
        return {"deleted": True}
    finally:
        db.close()


@router.patch("/{message_id}")
def update_message(conversation_id: str, message_id: str, payload: MessageUpdate) -> MessageOut:
    db = get_session()
    try:
        # Verify conversation exists
        conv = db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get message
        msg = db.get(Message, message_id)
        if not msg:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Verify message belongs to conversation
        if msg.conversation_id != conversation_id:
            raise HTTPException(status_code=404, detail="Message not found in conversation")
        
        # Update fields
        if payload.content_text is not None:
            msg.content_text = payload.content_text
        if payload.role is not None:
            msg.role = payload.role
        
        db.commit()
        db.refresh(msg)
        return MessageOut.model_validate(msg)
    finally:
        db.close()


@router.post("")
def create_message(conversation_id: str, payload: MessageCreate) -> MessageOut:
    db = get_session()
    try:
        # Verify conversation exists
        conv = db.get(Conversation, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Create new message
        msg = Message(
            conversation_id=conversation_id,
            role=payload.role,
            content_text=payload.content_text,
            model=payload.model,
            model_key=payload.model_key,
            status="completed"
        )
        
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return MessageOut.model_validate(msg)
    finally:
        db.close()
