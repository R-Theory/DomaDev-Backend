from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON, LargeBinary, Index, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .base import Base


def _id() -> str:
    return uuid.uuid4().hex


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    pinned = Column(Boolean, default=False, nullable=False)
    metadata_json = Column(JSON, nullable=True)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    conversation_id = Column(String(32), ForeignKey("conversations.id"), nullable=False)
    parent_id = Column(String(32), ForeignKey("messages.id"), nullable=True)

    role = Column(String(32), nullable=False)
    content_text = Column(Text, nullable=True)
    content_json = Column(JSON, nullable=True)

    model = Column(String(200), nullable=True)
    model_key = Column(String(64), nullable=True)

    system_prompt = Column(Text, nullable=True)
    temperature = Column(Integer, nullable=True)
    max_tokens = Column(Integer, nullable=True)

    upstream_id = Column(String(100), nullable=True)
    # Compressed raw payloads for space efficiency
    raw_request_gzip = Column(LargeBinary, nullable=True)
    raw_response_gzip = Column(LargeBinary, nullable=True)

    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    status = Column(String(32), default="completed", nullable=False)
    error_text = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    conversation = relationship("Conversation", back_populates="messages")


class MessageStream(Base):
    __tablename__ = "message_streams"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_id)
    message_id = Column(String(32), ForeignKey("messages.id"), nullable=False)
    raw_sse_gzip = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# Helpful indexes
Index("ix_messages_conversation", Message.conversation_id)
Index("ix_messages_started_at", Message.started_at)


